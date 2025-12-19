import cv2
import time
import threading
from typing import Dict
from config import (
    CAM_URLS, DETECTION_INTERVAL, CAMERA_OFFSET,
    NG_COOLDOWN, CONSECUTIVE_NG_THRESHOLD,
    OBSTACLE_ALERT_THRESHOLD, OBSTACLE_COOLDOWN_AFTER_ALERT
)
from detection import detect_and_classify
from alerts import sound_alert, email_alert, save_ng_image


class CameraManager:
    """Manages multiple camera streams and detection"""
    
    def __init__(self):
        self.num_cameras = len(CAM_URLS)
        
        # Frame storage
        self.latest_frames: Dict[int, any] = {i: None for i in range(self.num_cameras)}
        self.detected_frames: Dict[int, any] = {i: None for i in range(self.num_cameras)}
        self.detection_results: Dict[int, list] = {i: [] for i in range(self.num_cameras)}
        
        # Locks
        self.frame_locks: Dict[int, threading.Lock] = {
            i: threading.Lock() for i in range(self.num_cameras)
        }
        
        # NG tracking
        self.consecutive_ng_frames: Dict[int, int] = {i: 0 for i in range(self.num_cameras)}
        self.last_ng_save_time: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        self.ng_frame_lock = threading.Lock()
        self.ng_save_lock = threading.Lock()
        
        # Alert timestamps
        self.alert_timestamps: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        
        # Statistics
        self.ng_count_total: Dict[int, int] = {i: 0 for i in range(self.num_cameras)}
        self.ng_saved_count: Dict[int, int] = {i: 0 for i in range(self.num_cameras)}
        
        self.obstacle_count_total: Dict[int, int] = {i: 0 for i in range(self.num_cameras)}
        self.last_obstacle_time: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        
        self.obstacle_first_detected: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        self.obstacle_duration: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        self.obstacle_alert_triggered: Dict[int, bool] = {i: False for i in range(self.num_cameras)}
        self.last_obstacle_alert_time: Dict[int, float] = {i: 0 for i in range(self.num_cameras)}
        
        # Control
        self.stop_event = threading.Event()
        self.threads = []
    
    def start(self):
        """Start all camera reader threads"""
        print(f"\n{'='*60}")
        print(f"🚀 Starting Camera System")
        print(f"{'='*60}")
        
        for i, url in enumerate(CAM_URLS):
            thread = threading.Thread(
                target=self._camera_reader_thread,
                args=(i, url),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
        
        print(f"Started {self.num_cameras} camera threads")
        print(f"{'='*60}\n")
    
    def stop(self):
        """Stop all camera threads"""
        print("\n🛑 Stopping cameras...")
        self.stop_event.set()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2)
        
        print("✅ All cameras stopped")
        
        # Print statistics
        print(f"\n{'='*60}")
        print("📊 NG Detection Statistics")
        print(f"{'='*60}")
        for i in range(self.num_cameras):
            print(f"Camera {i+1}:")
            print(f"  Total NG detected: {self.ng_count_total[i]}")
            print(f"  Images saved: {self.ng_saved_count[i]}")
        print(f"{'='*60}\n")
    
    def _camera_reader_thread(self, camera_id: int, url: str):
        """
        Camera reader thread with detection
        
        Args:
            camera_id: Camera index
            url: RTSP URL
        """
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        if not cap.isOpened():
            print(f"❌ [Camera {camera_id+1}] Cannot open: {url}")
            return
        
        print(f"✅ [Camera {camera_id+1}] Started streaming from {url}")
        
        frame_count = 0
        detection_offset = camera_id * CAMERA_OFFSET
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        # Performance tracking
        last_log_time = time.time()
        frames_processed = 0
        
        while not self.stop_event.is_set():
            try:
                ret, frame = cap.read()
                
                if not ret or frame is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"⚠️ [Camera {camera_id+1}] Too many errors, reconnecting...")
                        cap.release()
                        time.sleep(2)
                        cap = cv2.VideoCapture(url)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cap.set(cv2.CAP_PROP_FPS, 15)
                        consecutive_errors = 0
                    time.sleep(0.1)
                    continue
                
                consecutive_errors = 0
                frames_processed += 1
                
                # Log FPS every 5 seconds
                current_time = time.time()
                if current_time - last_log_time >= 5.0:
                    fps = frames_processed / (current_time - last_log_time)
                    print(f"📊 [Camera {camera_id+1}] FPS: {fps:.1f}")
                    last_log_time = current_time
                    frames_processed = 0
                
                # Store latest frame
                with self.frame_locks[camera_id]:
                    self.latest_frames[camera_id] = frame.copy()
                
                # Run detection at intervals
                if (frame_count + detection_offset) % DETECTION_INTERVAL == 0:
                    try:
                        detection_start = time.time()
                        
                        # Run 3-stage detection
                        annotated_frame, detections, has_ng, has_obstacle = detect_and_classify(
                            frame, camera_id=camera_id
                        )
                        
                        detection_time = time.time() - detection_start
                        if detection_time > 1.0:
                            print(f"⚠️ [Camera {camera_id+1}] Slow detection: {detection_time:.2f}s")
                        
                        # Store results
                        with self.frame_locks[camera_id]:
                            self.detected_frames[camera_id] = annotated_frame
                            self.detection_results[camera_id] = detections
                            if has_ng or has_obstacle:
                                self.alert_timestamps[camera_id] = time.time()
                                
                        # Handle obstacle detection with timing
                        current_time = time.time()
                        
                        if has_obstacle:
                            if self.obstacle_first_detected[camera_id] == 0:
                                self.obstacle_first_detected[camera_id] = current_time
                                print(f"⏱️ [Camera {camera_id+1}] Obstacle detected - starting timer")
                            
                            duration = current_time - self.obstacle_first_detected[camera_id]
                            self.obstacle_duration[camera_id] = duration
                            
                            if duration >= OBSTACLE_ALERT_THRESHOLD:
                                time_since_last_alert = current_time - self.last_obstacle_alert_time[camera_id]
                                
                                if not self.obstacle_alert_triggered[camera_id] or \
                                   time_since_last_alert >= OBSTACLE_COOLDOWN_AFTER_ALERT:
                                    # Trigger alert!
                                    self.obstacle_count_total[camera_id] += 1
                                    self.last_obstacle_time[camera_id] = current_time
                                    self.obstacle_alert_triggered[camera_id] = True
                                    self.last_obstacle_alert_time[camera_id] = current_time
                                    
                                    print(f"🚨 [Camera {camera_id+1}] OBSTACLE ALERT! Duration: {duration:.1f}s")
                                    
                                    self._handle_obstacle_alert(
                                        camera_id,
                                        frame.copy(),
                                        annotated_frame.copy(),
                                        detections,
                                        duration
                                    )
                            else:
                                remaining = OBSTACLE_ALERT_THRESHOLD - duration
                                if int(remaining) % 10 == 0:
                                    print(f"⏱️ [Camera {camera_id+1}] Obstacle duration: {duration:.1f}s / {OBSTACLE_ALERT_THRESHOLD}s")
                        
                        else:
                            # ไม่เจอสิ่งกีดขวาง - reset timer
                            if self.obstacle_first_detected[camera_id] != 0:
                                print(f"✅ [Camera {camera_id+1}] Obstacle cleared (was detected for {self.obstacle_duration[camera_id]:.1f}s)")
                            
                            self.obstacle_first_detected[camera_id] = 0
                            self.obstacle_duration[camera_id] = 0
                            self.obstacle_alert_triggered[camera_id] = False
                        
                        # Handle NG detections
                        with self.ng_frame_lock:
                            if has_ng:
                                self.consecutive_ng_frames[camera_id] += 1
                                self.ng_count_total[camera_id] += 1
                                
                                # Save image and send alerts if threshold reached
                                if self.consecutive_ng_frames[camera_id] >= CONSECUTIVE_NG_THRESHOLD:
                                    self._handle_ng_detection(
                                        camera_id,
                                        frame.copy(),
                                        annotated_frame.copy(),
                                        detections
                                    )
                            else:
                                self.consecutive_ng_frames[camera_id] = 0
                        
                    except Exception as e:
                        print(f"❌ [Camera {camera_id+1}] Detection error: {e}")
                        with self.frame_locks[camera_id]:
                            self.detected_frames[camera_id] = frame.copy()
                else:
                    # Use previous detection frame if available
                    with self.frame_locks[camera_id]:
                        if self.detected_frames[camera_id] is None:
                            self.detected_frames[camera_id] = frame.copy()
                
                frame_count += 1
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ [Camera {camera_id+1}] Unexpected error: {e}")
                consecutive_errors += 1
                time.sleep(0.1)
        
        cap.release()
        print(f"✅ [Camera {camera_id+1}] Stopped (processed {frame_count} frames)")
    
    def _handle_ng_detection(self, camera_id, original_frame, annotated_frame, detections):
        """
        Handle NG detection: save image and send alerts
        
        Args:
            camera_id: Camera ID
            original_frame: Original frame
            annotated_frame: Annotated frame
            detections: List of detections
        """
        try:
            current_time = time.time()
            
            # Check cooldown
            with self.ng_save_lock:
                if current_time - self.last_ng_save_time[camera_id] < NG_COOLDOWN:
                    return
                self.last_ng_save_time[camera_id] = current_time
            
            # Save images
            image_paths, ng_detections = save_ng_image(
                original_frame,
                annotated_frame,
                camera_id,
                detections
            )
            
            if image_paths:
                self.ng_saved_count[camera_id] += 1
                
                # Play sound alert
                sound_alert.play(camera_id)
                
                # Send email alert (in background thread to avoid blocking)
                ng_count = len(ng_detections)
                threading.Thread(
                    target=email_alert.send_alert,
                    args=(camera_id, ng_count, image_paths, ng_detections),
                    daemon=True
                ).start()
            
        except Exception as e:
            print(f"❌ Error handling NG detection: {e}")
    
    def get_latest_frame(self, camera_id: int):
        """Get latest frame from camera"""
        if camera_id < 0 or camera_id >= self.num_cameras:
            return None
        
        with self.frame_locks[camera_id]:
            return self.latest_frames[camera_id]
    
    def get_detected_frame(self, camera_id: int):
        """Get latest detected frame from camera"""
        if camera_id < 0 or camera_id >= self.num_cameras:
            return None
        
        with self.frame_locks[camera_id]:
            return self.detected_frames[camera_id]
    
    def get_detections(self, camera_id: int):
        """Get current detections for camera"""
        if camera_id < 0 or camera_id >= self.num_cameras:
            return []
        
        with self.frame_locks[camera_id]:
            return self.detection_results[camera_id].copy()
    
    def has_recent_alert(self, camera_id: int, threshold_seconds=3):
        """Check if camera has recent alert"""
        if camera_id < 0 or camera_id >= self.num_cameras:
            return False
        
        current_time = time.time()
        last_alert = self.alert_timestamps.get(camera_id, 0)
        return (current_time - last_alert) < threshold_seconds
    
    def get_statistics(self, camera_id: int = None):
        """Get statistics for camera(s)"""
        if camera_id is not None:
            if camera_id < 0 or camera_id >= self.num_cameras:
                return None
            
            return {
                "camera_id": camera_id,
                "total_ng_detected": self.ng_count_total[camera_id],
                "images_saved": self.ng_saved_count[camera_id],
                "obstacle_detected": self.obstacle_count_total[camera_id],
                "obstacle_current_duration": round(self.obstacle_duration[camera_id], 1),
                "obstacle_alert_active": self.obstacle_alert_triggered[camera_id],
                "last_obstacle_time": self.last_obstacle_time[camera_id] if self.last_obstacle_time[camera_id] > 0 else None
            }
        else:
            # Return statistics for all cameras
            return {
                "cameras": [
                    {
                        "camera_id": i,
                        "total_ng_detected": self.ng_count_total[i],
                        "images_saved": self.ng_saved_count[i],
                        "obstacle_detected": self.obstacle_count_total[i],
                        "obstacle_current_duration": round(self.obstacle_duration[i], 1),
                        "obstacle_alert_active": self.obstacle_alert_triggered[i]
                    }
                    for i in range(self.num_cameras)
                ],
                "total_ng": sum(self.ng_count_total.values()),
                "total_saved": sum(self.ng_saved_count.values()),
                "total_obstacles": sum(self.obstacle_count_total.values())
            }
            
    def has_recent_obstacle(self, camera_id: int, threshold_seconds=5):
        """
        Check if camera has recent obstacle detection
        Returns True if obstacle has been detected for >= OBSTACLE_ALERT_THRESHOLD
        """
        if camera_id < 0 or camera_id >= self.num_cameras:
            return False
        
        return self.obstacle_alert_triggered[camera_id]
    
    def _handle_obstacle_alert(self, camera_id, original_frame, annotated_frame, detections, duration):
        """
        Handle obstacle alert: save image and send email
        
        Args:
            camera_id: Camera ID
            original_frame: Original frame
            annotated_frame: Annotated frame
            detections: List of detections
            duration: Duration of obstacle presence (seconds)
        """
        try:
            from alerts import save_obstacle_image, email_alert
            
            # Save images
            image_paths, obstacle_detections = save_obstacle_image(
                original_frame,
                annotated_frame,
                camera_id,
                detections,
                duration
            )
            
            if image_paths:
                # Send email alert (in background thread)
                obstacle_count = len(obstacle_detections)
                threading.Thread(
                    target=email_alert.send_obstacle_alert,
                    args=(camera_id, obstacle_count, image_paths, obstacle_detections, duration),
                    daemon=True
                ).start()
            
        except Exception as e:
            print(f"❌ Error handling obstacle alert: {e}")

    def get_obstacle_duration(self, camera_id: int):
        """Get current obstacle duration in seconds"""
        if camera_id < 0 or camera_id >= self.num_cameras:
            return 0
        
        return self.obstacle_duration[camera_id]

# Global camera manager instance
camera_manager = CameraManager()