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
from config import *
from routes import router
from Database.database import engine, get_db
import Database.models

# ---- APP SETUP ----
app = FastAPI(title="CCTV Camera API with Object Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router)

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
    try:
        with engine.connect() as conn:
            print(f"✅ Database connected successfully to {engine.url.database}")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        
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


# ---- STATIC FILES ----
static_path = Path("./out")
if static_path.exists():
    app.mount("/_next", StaticFiles(directory="./out/_next"), name="next-static")
    
    if (static_path / "images").exists():
        app.mount("/images", StaticFiles(directory="./out/images"), name="images")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)