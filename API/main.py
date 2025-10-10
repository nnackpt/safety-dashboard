from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import threading
import time
from typing import Dict, List
from pathlib import Path
from ultralytics import YOLO
import numpy as np
from datetime import datetime
import os
import pygame

# ---- CONFIG ----
CAM_URLS = [
    "rtsp://admin:@CCTV111@10.89.246.38:554/Streaming/Channels/101",
    "rtsp://admin:@CCTV111@10.89.246.31:554/Streaming/Channels/101",
]

ROI_ZONES = {
    0: [
        (242, 302),
        (418, 291),
        (626, 267),
        (800, 262),
        (963, 262),
        (1196, 260),
        (1419, 270),
        (1678, 284),
        (1880, 315),
        (1905, 312),
        (1916, 483),
        (1916, 708),
        (1908, 1071),
        (60, 1072),
        (3, 998),
        (0, 582),
        (156, 399),
    ],
    1: [
        (2, 1010),
        (194, 1052),
        (222, 937),
        (416, 944),
        (684, 947),
        (675, 872),
        (964, 845),
        (962, 815),
        (1082, 837),
        (1358, 965),
        (1706, 854),
        (1826, 799),
        (1874, 572),
        (1670, 374),
        (1504, 246),
        (1179, 221),
        (652, 205),
        (336, 213),
        (100, 246),
        (3, 364),
    ],
}

NOT_DETECTED_ROI_ZONES = {
    0: [
        (1176, 449),
        (1200, 386),
        (1208, 353),
        (1140, 349),
        (1086, 339),
        (1022, 341),
        (1008, 313),
        (976, 315),
        (976, 301),
        (890, 296),
        (891, 248),
        (836, 248),
        (800, 291),
        (771, 324),
        (724, 388),
        (692, 431),
        (675, 446),
        (686, 474),
        (722, 474),
        (686, 542),
        (654, 577),
        (620, 631),
        (674, 691),
        (740, 772),
        (754, 779),
        (780, 799),
        (1066, 872),
    ],
    1: [
        (808, 862),
        (1346, 799),
        (1377, 709),
        (1328, 617),
        (1268, 516),
        (1170, 386),
        (1132, 344),
        (982, 356),
        (879, 356),
    ],
}

DRAW_ROI = True
DRAW_EXCLUSION_ZONE = True

DUAL_W, DUAL_H = 760, 720
SINGLE_W, SINGLE_H = 1920, 1080

MODEL_PATH = "best.pt"
CONFIDENCE_THRESHOLD = 0.5

# ---- NG IMAGE SAVING CONFIG ----
NG_SAVE_DIR = "ng_images"  # โฟลเดอร์เก็บรูป NG
NG_COOLDOWN = 5  # วินาที - ระยะเวลาขั้นต่ำระหว่างการบันทึกภาพ
SAVE_ORIGINAL = True  # บันทึกภาพต้นฉบับ
SAVE_ANNOTATED = True  # บันทึกภาพ bounding box

os.makedirs(NG_SAVE_DIR, exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "original"), exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "annotated"), exist_ok=True)

# ---- SOUND ALERT CONFIG ----
ENABLE_SOUND_ALERT = True  # เปิด/ปิดเสียงแจ้งเตือน
SOUND_FILE = r"Sound Alarm\level-up-07-383747.mp3"
SOUND_COOLDOWN = 5

# ---- APP SETUP ----
app = FastAPI(title="CCTV Camera API with Object Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- GLOBAL STATE ----
latest_frames: Dict[int, any] = {i: None for i in range(len(CAM_URLS))}
detected_frames: Dict[int, any] = {i: None for i in range(len(CAM_URLS))}
detection_results: Dict[int, List] = {i: [] for i in range(len(CAM_URLS))}
frame_locks: Dict[int, threading.Lock] = {i: threading.Lock() for i in range(len(CAM_URLS))}
last_ng_save_time: Dict[int, float] = {i: 0 for i in range(len(CAM_URLS))}
ng_save_lock = threading.Lock()
stop_event = threading.Event()
last_sound_time: Dict[int, float] = {i: 0 for i in range(len(CAM_URLS))}
sound_lock = threading.Lock()

# Statistics
ng_count_total: Dict[int, int] = {i: 0 for i in range(len(CAM_URLS))}
ng_saved_count: Dict[int, int] = {i: 0 for i in range(len(CAM_URLS))}

# Load YOLO model
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ YOLO model loaded from {MODEL_PATH}")
    print(f"📋 Classes: {model.names}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")
    model = None

# ---- DETECTION FUNCTION ----
def is_point_in_polygon(point, polygon):
    x, y = point
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def save_ng_image(original_frame, annotated_frame, camera_id, detections):
    """Save NG images with timestamp"""
    try:
        current_time = time.time()
        
        # ตรวจสอบ cooldown
        with ng_save_lock:
            if current_time - last_ng_save_time[camera_id] < NG_COOLDOWN:
                return False
            last_ng_save_time[camera_id] = current_time
        
        # สร้าง timestamp สำหรับชื่อไฟล์
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # นับจำนวน NG ในภาพ
        ng_detections = [d for d in detections if d['class'].strip().upper() == 'NG']
        ng_count = len(ng_detections)
        
        base_filename = f"cam{camera_id+1}_ng{ng_count}_{timestamp}"
        
        # บันทึกภาพต้นฉบับ
        if SAVE_ORIGINAL:
            original_path = os.path.join(NG_SAVE_DIR, "original", f"{base_filename}_orig.jpg")
            cv2.imwrite(original_path, original_frame)
        
        # บันทึกภาพที่มี annotation
        if SAVE_ANNOTATED:
            annotated_path = os.path.join(NG_SAVE_DIR, "annotated", f"{base_filename}_anno.jpg")
            
            info_frame = annotated_frame.copy()
            
            cv2.rectangle(info_frame, (10, 10), (600, 120), (0, 0, 0), -1)
            cv2.rectangle(info_frame, (10, 10), (600, 120), (0, 0, 255), 3)
            
            cv2.putText(info_frame, f"NG DETECTED - Camera {camera_id+1}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(info_frame, f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(info_frame, f"NG Count: {ng_count}", (20, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imwrite(annotated_path, info_frame)
        
        ng_saved_count[camera_id] += 1
        
        print(f"📸 [Camera {camera_id+1}] NG image saved: {base_filename} (Total NG: {ng_count})")
        return True
        
    except Exception as e:
        print(f"❌ Error saving NG image: {e}")
        return False

def draw_detections(frame, results, camera_id=0):
    """Draw bounding boxes and labels on frame with ROI filtering and exclusion zones"""
    annotated_frame = frame.copy()
    detections = []
    has_ng = False
    
    # วาดเส้นขอบเขต ROI (พื้นที่ตรวจจับ - สีแดง)
    if DRAW_ROI and camera_id in ROI_ZONES:
        roi = ROI_ZONES[camera_id]
        pts = np.array(roi, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(annotated_frame, [pts], True, (0, 0, 255), 3)
        cv2.putText(annotated_frame, "DETECTION ZONE", (roi[0][0], roi[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # วาดเส้นขอบเขต NOT_DETECTED_ROI_ZONES (พื้นที่ยกเว้น - สีส้ม)
    if DRAW_EXCLUSION_ZONE and camera_id in NOT_DETECTED_ROI_ZONES:
        exclusion_roi = NOT_DETECTED_ROI_ZONES[camera_id]
        pts = np.array(exclusion_roi, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(annotated_frame, [pts], True, (0, 255, 255), 3)
        cv2.putText(annotated_frame, "NON-DETECTION ZONE", 
                    (exclusion_roi[0][0], exclusion_roi[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            
            if conf < CONFIDENCE_THRESHOLD:
                continue
            
            # คำนวณจุดกึ่งกลาง
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            
            # ตรวจสอบว่าอยู่ใน ROI หลักหรือไม่
            if camera_id in ROI_ZONES:
                if not is_point_in_polygon((center_x, center_y), ROI_ZONES[camera_id]):
                    continue  # ไม่อยู่ใน ROI หลัก ข้ามไป
            
            # ตรวจสอบว่าอยู่ใน NOT_DETECTED_ROI_ZONES หรือไม่
            if camera_id in NOT_DETECTED_ROI_ZONES:
                if is_point_in_polygon((center_x, center_y), NOT_DETECTED_ROI_ZONES[camera_id]):
                    continue  # อยู่ในพื้นที่ยกเว้น ข้ามไป (ไม่ตรวจจับ)
            
            class_name = model.names[cls] if model else f"class_{cls}"
            is_ng = class_name.strip().upper() == "NG"
            
            # ถ้าเจอ NG
            if is_ng:
                has_ng = True
                ng_count_total[camera_id] += 1
            
            color = (0, 0, 255) if is_ng else (0, 255, 0)
            
            detections.append({
                "class": class_name,
                "confidence": round(conf, 2),
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            })
            
            # วาด bounding box (หนาขึ้นถ้าเป็น NG)
            thickness = 4 if is_ng else 2
            cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
            
            # วาด label
            label = f"{class_name} {conf:.2f}"
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (int(x1), int(y1) - label_h - 10), 
                          (int(x1) + label_w, int(y1)), color, -1)
            cv2.putText(annotated_frame, label, (int(x1), int(y1) - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # วาดจุดกึ่งกลาง (debug)
            cv2.circle(annotated_frame, (center_x, center_y), 5, color, -1)
    
    return annotated_frame, detections, has_ng

# ---- CAMERA READER WITH DETECTION ----
def camera_reader_with_detection(index: int, url: str):
    """Read frames from camera and run object detection"""
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print(f"[Camera {index}] Cannot open: {url}")
        return
    
    print(f"[Camera {index}] Started streaming from {url}")
    frame_count = 0
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.1)
            continue
        
        # Store original frame
        with frame_locks[index]:
            latest_frames[index] = frame.copy()
        
        if model is not None:
            try:
                # Run YOLO inference
                results = model(frame, verbose=False)
                
                # Draw detections on frame
                annotated_frame, detections, has_ng = draw_detections(frame, results, camera_id=index)
                
                # Store detected frame and results
                with frame_locks[index]:
                    detected_frames[index] = annotated_frame
                    detection_results[index] = detections
                
                # บันทึกภาพถ้าเจอ NG
                if has_ng:
                    save_ng_image(frame.copy(), annotated_frame.copy(), index, detections)
                    play_alert_sound(index)
                    
            except Exception as e:
                print(f"[Camera {index}] Detection error: {e}")
                with frame_locks[index]:
                    detected_frames[index] = frame.copy()
                    detection_results[index] = []
        else:
            with frame_locks[index]:
                detected_frames[index] = frame.copy()
                detection_results[index] = []
        
        frame_count += 1
        time.sleep(0)
    
    cap.release()
    print(f"[Camera {index}] Stopped (processed {frame_count} frames)")
    
# ---- Initialize pygame mixer ----
if ENABLE_SOUND_ALERT:
    try:
        pygame.mixer.init()
        if os.path.exists(SOUND_FILE):
            alert_sound = pygame.mixer.Sound(SOUND_FILE)
            print(f"✅ Sound alert loaded: {SOUND_FILE}")
        else:
            alert_sound = None
            print(f"⚠️ Sound file not found: {SOUND_FILE}")
    except Exception as e:
        alert_sound = None
        print(f"❌ Error loading sound: {e}")
else:
    alert_sound = None

def play_alert_sound(camera_id):
    """Play alert sound with cooldown"""
    if not ENABLE_SOUND_ALERT or alert_sound is None:
        return False
    
    try:
        current_time = time.time()
        
        with sound_lock:
            if current_time - last_sound_time[camera_id] < SOUND_COOLDOWN:
                return False
            last_sound_time[camera_id] = current_time
        
        # เล่นเสียงแบบ non-blocking
        alert_sound.play()
        print(f"🔔 [Camera {camera_id+1}] Alert sound played")
        return True
        
    except Exception as e:
        print(f"❌ Error playing sound: {e}")
        return False

# ---- STARTUP/SHUTDOWN ----
@app.on_event("startup")
async def startup_event():
    """Start all camera reader threads"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting CCTV System")
    print(f"{'='*60}")
    print(f"NG Images Directory: {os.path.abspath(NG_SAVE_DIR)}")
    print(f"NG Cooldown: {NG_COOLDOWN} seconds")
    print(f"Save Original: {SAVE_ORIGINAL}")
    print(f"Save Annotated: {SAVE_ANNOTATED}")
    print(f"{'='*60}\n")
    
    for i, url in enumerate(CAM_URLS):
        t = threading.Thread(target=camera_reader_with_detection, args=(i, url), daemon=True)
        t.start()
    print(f"Started {len(CAM_URLS)} camera threads with object detection\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop all camera threads"""
    stop_event.set()
    
    print(f"\n{'='*60}")
    print("📊 NG Detection Statistics")
    print(f"{'='*60}")
    for i in range(len(CAM_URLS)):
        print(f"Camera {i+1}:")
        print(f"  Total NG detected: {ng_count_total[i]}")
        print(f"  Images saved: {ng_saved_count[i]}")
    print(f"{'='*60}\n")
    print("Shutting down cameras")

# ---- API ENDPOINTS ----
@app.get("/api")
async def root():
    """API info"""
    return {
        "message": "CCTV Camera API with Object Detection",
        "cameras": len(CAM_URLS),
        "model": MODEL_PATH,
        "model_loaded": model is not None,
        "classes": model.names if model else {},
        "ng_save_dir": NG_SAVE_DIR,
        "endpoints": [
            "GET /api/cameras - List all cameras",
            "GET /api/camera/{camera_id} - Camera info",
            "GET /api/camera/{camera_id}/stream - Video stream (original)",
            "GET /api/camera/{camera_id}/stream/detected - Video stream with detections",
            "GET /api/camera/{camera_id}/detections - Current detections",
            "GET /api/camera/{camera_id}/snapshot - Get single frame",
            "GET /api/statistics - Get NG detection statistics",
            "GET /api/ng-images - List saved NG images"
        ]
    }

@app.get("/api/cameras")
async def get_cameras():
    """Get list of all cameras with status"""
    cameras = []
    for i in range(len(CAM_URLS)):
        with frame_locks[i]:
            status = "active" if latest_frames[i] is not None else "inactive"
            num_detections = len(detection_results[i])
        cameras.append({
            "id": i,
            "url": CAM_URLS[i],
            "status": status,
            "detections": num_detections,
            "ng_detected": ng_count_total[i],
            "ng_saved": ng_saved_count[i]
        })
    return {"cameras": cameras}

@app.get("/api/camera/{camera_id}")
async def get_camera_info(camera_id: int):
    """Get specific camera information"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    with frame_locks[camera_id]:
        frame = latest_frames[camera_id]
        status = "active" if frame is not None else "inactive"
        height, width = frame.shape[:2] if frame is not None else (0, 0)
        num_detections = len(detection_results[camera_id])
    
    return {
        "id": camera_id,
        "url": CAM_URLS[camera_id],
        "status": status,
        "resolution": f"{width}x{height}",
        "detections": num_detections,
        "ng_detected": ng_count_total[camera_id],
        "ng_saved": ng_saved_count[camera_id]
    }

@app.get("/api/camera/{camera_id}/detections")
async def get_detections(camera_id: int):
    """Get current detections for a camera"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    with frame_locks[camera_id]:
        detections = detection_results[camera_id].copy()
    
    # นับจำนวน NG
    ng_count = sum(1 for d in detections if d['class'].strip().upper() == 'NG')
    
    return {
        "camera_id": camera_id,
        "count": len(detections),
        "ng_count": ng_count,
        "detections": detections
    }

@app.get("/api/statistics")
async def get_statistics():
    """Get NG detection statistics"""
    stats = []
    for i in range(len(CAM_URLS)):
        stats.append({
            "camera_id": i,
            "camera_name": f"Camera {i+1}",
            "total_ng_detected": ng_count_total[i],
            "images_saved": ng_saved_count[i]
        })
    
    return {
        "statistics": stats,
        "total_ng": sum(ng_count_total.values()),
        "total_saved": sum(ng_saved_count.values()),
        "save_directory": os.path.abspath(NG_SAVE_DIR)
    }

@app.get("/api/ng-images")
async def list_ng_images():
    """List all saved NG images"""
    images = {
        "original": [],
        "annotated": []
    }
    
    # List original images
    original_dir = os.path.join(NG_SAVE_DIR, "original")
    if os.path.exists(original_dir):
        for filename in sorted(os.listdir(original_dir), reverse=True):
            if filename.endswith(('.jpg', '.png')):
                file_path = os.path.join(original_dir, filename)
                file_stat = os.stat(file_path)
                images["original"].append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })
    
    # List annotated images
    annotated_dir = os.path.join(NG_SAVE_DIR, "annotated")
    if os.path.exists(annotated_dir):
        for filename in sorted(os.listdir(annotated_dir), reverse=True):
            if filename.endswith(('.jpg', '.png')):
                file_path = os.path.join(annotated_dir, filename)
                file_stat = os.stat(file_path)
                images["annotated"].append({
                    "filename": filename,
                    "path": file_path,
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })
    
    return {
        "total_images": len(images["original"]) + len(images["annotated"]),
        "images": images
    }

@app.get("/api/camera/{camera_id}/stream")
async def video_stream(camera_id: int, single: bool = False):
    """Stream original video from specific camera (MJPEG)"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    target_w = SINGLE_W if single else DUAL_W
    target_h = SINGLE_H if single else DUAL_H
    
    def generate():
        while True:
            with frame_locks[camera_id]:
                frame = latest_frames[camera_id]
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            resized = cv2.resize(frame, (target_w, target_h))
            
            _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)
    
    return StreamingResponse(
        generate(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/{camera_id}/stream/detected")
async def video_stream_detected(camera_id: int, single: bool = False):
    """Stream video with object detection overlays (MJPEG)"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    target_w = SINGLE_W if single else DUAL_W
    target_h = SINGLE_H if single else DUAL_H
    
    def generate():
        while True:
            with frame_locks[camera_id]:
                frame = detected_frames[camera_id]
            
            if frame is None:
                time.sleep(0.1)
                continue
            
            resized = cv2.resize(frame, (target_w, target_h))
            
            _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)
    
    return StreamingResponse(
        generate(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/camera/{camera_id}/snapshot")
async def get_snapshot(camera_id: int, detected: bool = False, single: bool = False):
    """Get single frame as JPEG image"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    with frame_locks[camera_id]:
        frame = detected_frames[camera_id] if detected else latest_frames[camera_id]
    
    if frame is None:
        return {"error": "No frame available"}
    
    target_w = SINGLE_W if single else DUAL_W
    target_h = SINGLE_H if single else DUAL_H
    
    resized = cv2.resize(frame, (target_w, target_h))
    _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    return StreamingResponse(
        iter([buffer.tobytes()]), 
        media_type="image/jpeg"
    )

# ---- STATIC FILES ----
static_path = Path("./out")
if static_path.exists():
    app.mount("/_next", StaticFiles(directory="./out/_next"), name="next-static")
    
    if (static_path / "images").exists():
        app.mount("/images", StaticFiles(directory="./out/images"), name="images")
    
    for item in static_path.glob("*.png"):
        @app.get(f"/{item.name}")
        async def serve_static_file(filename: str = item.name):
            return FileResponse(static_path / filename)
    
    for item in static_path.glob("*.jpg"):
        @app.get(f"/{item.name}")
        async def serve_static_file(filename: str = item.name):
            return FileResponse(static_path / filename)
    
    @app.get("/{full_path:path}")
    async def serve_nextjs(full_path: str):
        file_path = static_path / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        
        html_path = static_path / f"{full_path}.html"
        if html_path.is_file():
            return FileResponse(html_path)
        
        return FileResponse(static_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)