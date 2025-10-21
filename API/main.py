from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import threading
import time
from typing import Dict, List, Optional
from pathlib import Path
from ultralytics import YOLO
import numpy as np
from datetime import datetime
import os
import pygame
import torch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
import pyodbc
from dotenv import load_dotenv

load_dotenv()

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
USE_HALF_PRECISION = True

print(f"🖥️  Device: {DEVICE}")
if DEVICE == 'cuda':
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM Available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# ---- CONFIG ----
CAM_URLS = [
    "rtsp://admin:@CCTV111@10.89.246.38:554/Streaming/Channels/101",
    "rtsp://admin:@CCTV111@10.89.246.31:554/Streaming/Channels/101",
]

ROI_ZONES = {
    0: [
        (10, 599),
        (240, 311),
        (663, 258),
        (828, 251),
        (1038, 260),
        (1592, 326),
        (1912, 391),
        (1911, 1073),
        (144, 1077),
        (9, 934),
    ],
    1: [
        (9, 1007),
        (204, 1057),
        (496, 1077),
        (693, 1068),
        (682, 862),
        (970, 847),
        (969, 784),
        (1104, 765),
        (1095, 842),
        (1107, 859),
        (1107, 909),
        (1131, 954),
        (1167, 947),
        (1167, 930),
        (1251, 917),
        (1281, 924),
        (1306, 967),
        (1362, 965),
        (1605, 892),
        (1826, 797),
        (1868, 770),
        (1767, 647),
        (1472, 353),
        (1156, 349),
        (664, 344),
        (232, 364),
        (150, 371),
        (6, 591),
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
SINGLE_W, SINGLE_H = 1024, 768

MODEL_PATH = r"new_models\train7.pt"
CONFIDENCE_THRESHOLD = 0.7

NMS_IOU_THRESHOLD = 0.25  # IoU threshold สำหรับ NMS
CLASSIFICATION_THRESHOLD = 0.6  # Confidence threshold สำหรับ classification
ENABLE_NMS = False

# ---- NG IMAGE SAVING CONFIG ----
NG_SAVE_DIR = "ng_images"  # โฟลเดอร์เก็บรูป NG
NG_COOLDOWN = 5  # วินาที - ระยะเวลาขั้นต่ำระหว่างการบันทึกภาพ
SAVE_ORIGINAL = True  # บันทึกภาพต้นฉบับ
SAVE_ANNOTATED = True  # บันทึกภาพ bounding box

os.makedirs(NG_SAVE_DIR, exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "original"), exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "annotated"), exist_ok=True)

# ---- SOUND ALERT CONFIG ----
ENABLE_SOUND_ALERT = True
SOUND_FILE = r"Sound Alarm\emergency-alarmsiren-type.mp3"
SOUND_COOLDOWN = 10

# ---- CLASSIFICATION MODEL CONFIG ----
CLASSIFICATION_MODEL_PATH = r"new_models\classification_train6.pt"
ENABLE_CLASSIFICATION = True

# ---- PERSON ----
PERSON_MODEL_PATH = r"new_models\person.pt"

# ---- TRACKING CONFIG ----
ENABLE_TRACKING = True  # เปิด/ปิด tracking
TRACK_ALERT_COOLDOWN = 60
TRACKER_TYPE = "bytetrack.yaml"  # หรือ "botsort.yaml"

# ---- EMAIL ALERT CONFIG ----
ENABLE_EMAIL_ALERT = True
EMAIL_COOLDOWN = 300  # 5 นาที

DETECTION_INTERVAL = 10  # ตรวจจับทุก N เฟรม แทน ทุกเฟรม
CAMERA_OFFSET = 5

# Outlook/Office365 SMTP Settings
SMTP_SERVER = "smtp.alv.autoliv.int"
SMTP_PORT = 25
SENDER_EMAIL = "TCS-PPE-Safety@autoliv.com"
SENDER_PASSWORD = ""
SENDER_NAME = "PPE-Safety Alert"

RECIPIENT_EMAILS = [
    "kittisak.wongprachanukul@autoliv.com"
]

CC_EMAILS = [
    "phakin.thongla-ar.external@autoliv.com", 
    "kuntika.prasitnawa.external@autoliv.com",
    "rutthaya.larot@autoliv.com"
]

CLASS_MAPPING = {
    'hand': ['non-safety-glove', 'safety-glove'],
    'shoe': ['non-safety-shoe','safety-shoe'],
    'glasses': ['non-safety-glasses', 'safety-glasses'],
    'shirt': ['non-safety-shirt', 'safety-shirt']
}

# ---- DATABASE CONFIG ----
DB_CONFIG = {
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_NAME'),
    'username': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'driver': os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
}

def get_db_connection():
    """สร้าง connection ไปยัง SQL Server"""
    try:
        conn_str = (
            f"DRIVER={{{DB_CONFIG['driver']}}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def test_db_connection():
    """ทดสอบการเชื่อมต่อ database"""
    conn = get_db_connection()
    if conn:
        print("✅ Database connected successfully!")
        conn.close()
        return True
    return False

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
alert_timestamps: Dict[int, float] = {i: 0 for i in range(len(CAM_URLS))}
tracked_alerts: Dict[int, Dict[int, float]] = {i: {} for i in range(len(CAM_URLS))}
TRACK_ALERT_COOLDOWN = 60
last_email_time: Dict[int, float] = {i: 0 for i in range(len(CAM_URLS))}
email_lock = threading.Lock()

# Statistics
ng_count_total: Dict[int, int] = {i: 0 for i in range(len(CAM_URLS))}
ng_saved_count: Dict[int, int] = {i: 0 for i in range(len(CAM_URLS))}

# Load Person Detection model
person_model = None
try:
    person_model = YOLO(PERSON_MODEL_PATH)
    person_model.to(DEVICE)
    
    if DEVICE == 'cuda' and USE_HALF_PRECISION:
        person_model.model.half()
    
    print(f"✅ Person Detection model loaded from {PERSON_MODEL_PATH}")
    print(f"📋 Person Classes: {person_model.names}")
except Exception as e:
    print(f"❌ Error loading Person model: {e}")
    person_model = None

# Load YOLO model
try:
    model = YOLO(MODEL_PATH)
    model.to(DEVICE)
    
    if DEVICE == 'cuda' and USE_HALF_PRECISION:
        model.model.half()
    
    print(f"✅ YOLO Detection model loaded from {MODEL_PATH}")
    print(f"📍 Running on: {DEVICE}")
    print(f"📋 Detection Classes: {model.names}")
except Exception as e:
    print(f"❌ Error loading YOLO Detection model: {e}")
    model = None

# Load Classification model
classification_model = None
if ENABLE_CLASSIFICATION:
    try:
        classification_model = YOLO(CLASSIFICATION_MODEL_PATH)
        classification_model.to(DEVICE)
        
        if DEVICE == 'cuda' and USE_HALF_PRECISION:
            classification_model.model.half()
        
        print(f"✅ YOLO Classification model loaded from {CLASSIFICATION_MODEL_PATH}")
        print(f"📍 Running on: {DEVICE}")
        print(f"📋 Classification Classes: {classification_model.names}")
    except Exception as e:
        print(f"❌ Error loading Classification model: {e}")
        classification_model = None

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

def send_email_alert(camera_id, ng_count, image_paths, ng_detections):
    """ส่งอีเมลแจ้งเตือน NG พร้อมแสดงรูปภาพ inline และรายละเอียด detections"""
    if not ENABLE_EMAIL_ALERT:
        return False
    
    try:
        current_time = time.time()
        
        with email_lock:
            if current_time - last_email_time[camera_id] < EMAIL_COOLDOWN:
                print(f"⏳ [Camera {camera_id+1}] Email cooldown active, skipping...")
                return False
            last_email_time[camera_id] = current_time
        
        # ⭐ สร้างรายการ detections แบบจัดกลุ่มตาม class
        detection_summary = {}
        for d in ng_detections:
            classified_as = d.get('classified_as', 'unknown')
            if classified_as not in detection_summary:
                detection_summary[classified_as] = 0
            detection_summary[classified_as] += 1
        
        # สร้าง HTML สำหรับแสดง detection details
        detection_html = ""
        for class_name, count in detection_summary.items():
            # แปลงชื่อให้อ่านง่าย เช่น non-safety-glove → Non-Safety Glove
            display_name = class_name.replace('-', ' ').title()
            detection_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; background-color: #ffe6e6;">
                    <span style="color: #ff0000; font-weight: bold;">⚠️ {display_name}</span>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #ff0000;">
                    {count}
                </td>
            </tr>
            """
        
        # สร้าง email message
        msg = MIMEMultipart('related')
        msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg['To'] = ', '.join(RECIPIENT_EMAILS)
        msg['Cc'] = ', '.join(CC_EMAILS)
        msg['Subject'] = f"⚠️ NG Detected - Camera {camera_id+1} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        # สร้าง HTML body
        annotated_path = image_paths.get('annotated')
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #ff0000; color: white; padding: 20px; border-radius: 5px;">
                    <h2>🚨 NG Detection Alert</h2>
                </div>
                <div style="padding: 20px;">
                    <p><strong>Camera:</strong> Camera {camera_id+1}</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Total NG/Non-Safety Count:</strong> <span style="color: red; font-size: 24px; font-weight: bold;">{ng_count}</span></p>
                    <p><strong>Location:</strong> Slitting Process</p>
                </div>
                
                <div style="padding: 20px;">
                    <h3>📋 Detection Details:</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                        <thead>
                            <tr style="background-color: #f0f0f0;">
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Item Type</th>
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detection_html}
                        </tbody>
                    </table>
                </div>
                
                <div style="padding: 20px;">
                    <h3>📸 Detection Image:</h3>
        """
        
        if annotated_path and os.path.exists(annotated_path):
            html_body += '<img src="cid:detection_image" style="max-width: 800px; width: 100%; border: 3px solid #ff0000; margin: 10px 0; display: block;"><br>'
        else:
            html_body += '<p style="color: red;">⚠️ No detection image available</p>'
        
        html_body += """
                </div>
                <div style="background-color: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 5px;">
                    <p style="color: #666; font-size: 12px;">
                        This is an automated alert from CCTV Monitoring System.<br>
                        Please check the cameras immediately and ensure proper PPE usage.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # ⭐ สำคัญ: ต้อง attach HTML body ก่อน
        msg.attach(MIMEText(html_body, 'html'))
        
        # ⭐ แล้วค่อย attach รูปภาพ (inline)
        if annotated_path and os.path.exists(annotated_path):
            with open(annotated_path, 'rb') as f:
                img_data = f.read()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<detection_image>')
                image.add_header('Content-Disposition', 'inline', filename=os.path.basename(annotated_path))
                msg.attach(image)
            
            print(f"📎 [Camera {camera_id+1}] Attached inline image: {os.path.basename(annotated_path)}")
        
        all_recipients = RECIPIENT_EMAILS + CC_EMAILS
        
        # ส่งอีเมล
        print(f"📧 [Camera {camera_id+1}] Connecting to SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SENDER_PASSWORD:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
        
        # แสดงรายละเอียดที่ส่งไป
        print(f"✅ [Camera {camera_id+1}] Email alert sent with detection details:")
        for class_name, count in detection_summary.items():
            print(f"   - {class_name}: {count}")
        
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Email authentication failed. Check your email/password")
        return False
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def save_ng_image(original_frame, annotated_frame, camera_id, detections):
    """Save NG images with timestamp and insert to database"""
    try:
        current_time = time.time()
        
        with ng_save_lock:
            if current_time - last_ng_save_time[camera_id] < NG_COOLDOWN:
                return False
            last_ng_save_time[camera_id] = current_time
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        ng_detections = [d for d in detections 
                        if d.get('classified_as', '').strip().upper() == 'NG' 
                        or 'non-safety' in d.get('classified_as', '').lower()]
        ng_count = len(ng_detections)
        
        base_filename = f"cam{camera_id+1}_ng{ng_count}_{timestamp}"
        
        # บันทึกรูปภาพ
        original_path = None
        annotated_path = None
        
        if SAVE_ORIGINAL:
            original_path = os.path.join(NG_SAVE_DIR, "original", f"{base_filename}_orig.jpg")
            cv2.imwrite(original_path, original_frame)
        
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
        
        # ⭐ บันทึกลง Database
        ticket_id = insert_ng_ticket_to_db(camera_id, ng_detections, annotated_path, original_path)
        
        print(f"📸 [Camera {camera_id+1}] NG saved: {base_filename} | DB Ticket: {ticket_id}")
        
        image_paths = {}
        if SAVE_ORIGINAL:
            image_paths['original'] = original_path
        if SAVE_ANNOTATED:
            image_paths['annotated'] = annotated_path
        
        send_email_alert(camera_id, ng_count, image_paths, ng_detections)
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving NG image: {e}")
        return False
    
def insert_ng_ticket_to_db(camera_id, ng_detections, annotated_path, original_path):
    """บันทึก NG Ticket และ Evidence ลง Database"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database")
        return None
    
    try:
        cursor = conn.cursor()
        
        # 1. สร้าง NG Ticket
        detected_time = datetime.now()
        location = f"Camera {camera_id + 1} - Slitting Process"
        
        # สร้างรายละเอียด detection
        details = ", ".join([f"{d.get('classified_as')}" for d in ng_detections])
        
        insert_ticket = """
        INSERT INTO ppe_NGTicket 
        (DetectedTime, Location, RuleID, Severity, Status, NotifiedEmail, CreatedBy, CreatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_ticket, (
            detected_time,
            location,
            1,  # RuleID - ปรับตามกฎที่ต้องการ
            'High',  # Severity
            'Open',  # Status
            ','.join(RECIPIENT_EMAILS),
            'CCTV_System',
            detected_time
        ))
        
        # ดึง TicketID ที่เพิ่งสร้าง
        cursor.execute("SELECT @@IDENTITY AS TicketID")
        ticket_id = cursor.fetchone()[0]
        
        # 2. บันทึกไฟล์หลักฐาน
        if annotated_path:
            insert_evidence = """
            INSERT INTO ppe_NGEvidence (TicketID, FilePath, FileType, CreatedAt)
            VALUES (?, ?, ?, ?)
            """
            cursor.execute(insert_evidence, (
                ticket_id,
                annotated_path,
                'annotated',
                detected_time
            ))
        
        if original_path:
            cursor.execute(insert_evidence, (
                ticket_id,
                original_path,
                'original',
                detected_time
            ))
        
        conn.commit()
        print(f"✅ Ticket {ticket_id} saved to database")
        
        return ticket_id
        
    except Exception as e:
        print(f"❌ Database insert error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def classify_object(frame, bbox, detected_class):
    """Classify cropped object using classification model"""
    if classification_model is None or not ENABLE_CLASSIFICATION:
        return detected_class, 0.0, False  # เพิ่ม flag ว่า classify สำเร็จหรือไม่
    
    # ตรวจสอบว่า class นี้ต้องการ classification หรือไม่
    base_class = detected_class.lower()
    if base_class not in CLASS_MAPPING:
        return detected_class, 0.0, False
    
    try:
        x1, y1, x2, y2 = bbox
        
        # ขยาย bbox เล็กน้อย
        padding = 10
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(frame.shape[1], x2 + padding)
        y2 = min(frame.shape[0], y2 + padding)
        
        # Crop object
        cropped = frame[y1:y2, x1:x2]
        
        if cropped.size == 0:
            print(f"⚠️ Empty crop for {detected_class}")
            return detected_class, 0.0, False
        
        # Run classification
        results = classification_model(cropped, device=DEVICE, verbose=False)
        
        if len(results) > 0 and len(results[0].probs) > 0:
            probs = results[0].probs
            relevant_classes = CLASS_MAPPING.get(base_class, [])
            
            # หา best match จาก relevant classes
            best_conf = 0
            best_class = None
            
            for idx, conf in enumerate(probs.data):
                class_name = classification_model.names[idx]
                conf_value = float(conf)
                
                if class_name in relevant_classes and conf_value > best_conf:
                    best_conf = conf_value
                    best_class = class_name
            
            if best_class is not None:
                # 🔍 Debug log
                print(f"✅ Classified {detected_class} → {best_class} (conf: {best_conf:.2f})")
                return best_class, best_conf, True
            else:
                print(f"⚠️ No relevant class found for {detected_class}")
        
        return detected_class, 0.0, False
        
    except Exception as e:
        print(f"❌ Classification error for {detected_class}: {e}")
        return detected_class, 0.0, False

def detect_ppe_in_person(frame, person_bbox):
    """
    Detect PPE (hand, shoe, glasses, shirt) within person bounding box
    Returns list of detections with adjusted coordinates
    """
    if model is None:
        return []
    
    try:
        x1, y1, x2, y2 = map(int, person_bbox)
        
        # Crop person region with padding
        padding = 20
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(frame.shape[1], x2 + padding)
        y2 = min(frame.shape[0], y2 + padding)
        
        person_crop = frame[y1:y2, x1:x2]
        
        if person_crop.size == 0:
            return []
        
        # Run PPE detection on cropped image
        ppe_results = model(
            person_crop,
            device=DEVICE,
            verbose=False,
            half=USE_HALF_PRECISION
        )
        
        # Adjust coordinates back to original frame
        detections = []
        for result in ppe_results:
            if len(result.boxes) == 0:
                continue
                
            for box in result.boxes:
                conf = float(box.conf)
                if conf < CONFIDENCE_THRESHOLD:
                    continue
                
                # Get bbox in crop coordinates
                crop_x1, crop_y1, crop_x2, crop_y2 = box.xyxy[0].cpu().numpy()
                
                # Convert to original frame coordinates
                orig_x1 = int(crop_x1 + x1)
                orig_y1 = int(crop_y1 + y1)
                orig_x2 = int(crop_x2 + x1)
                orig_y2 = int(crop_y2 + y1)
                
                cls = int(box.cls)
                class_name = model.names[cls]
                
                detections.append({
                    'bbox': [orig_x1, orig_y1, orig_x2, orig_y2],
                    'conf': conf,
                    'class': class_name,
                    'cls': cls
                })
        
        return detections
        
    except Exception as e:
        print(f"❌ Error in detect_ppe_in_person: {e}")
        return []

def draw_detections_3stage(frame, person_results, camera_id=0):
    """
    3-Stage Detection: Person → PPE Detection → Classification
    """
    annotated_frame = frame.copy()
    detections = []
    has_ng = False
    alert_timestamp = None
    
    # วาด ROI zones (เหมือนเดิม)
    if DRAW_ROI and camera_id in ROI_ZONES:
        roi = ROI_ZONES[camera_id]
        pts = np.array(roi, np.int32).reshape((-1, 1, 2))
        cv2.polylines(annotated_frame, [pts], True, (0, 0, 255), 3)
        cv2.putText(annotated_frame, "DETECTION ZONE", (roi[0][0], roi[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    if DRAW_EXCLUSION_ZONE and camera_id in NOT_DETECTED_ROI_ZONES:
        exclusion_roi = NOT_DETECTED_ROI_ZONES[camera_id]
        pts = np.array(exclusion_roi, np.int32).reshape((-1, 1, 2))
        cv2.polylines(annotated_frame, [pts], True, (0, 255, 255), 3)
        cv2.putText(annotated_frame, "NON-DETECTION ZONE",
                    (exclusion_roi[0][0], exclusion_roi[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # ⭐ STAGE 1: Process each detected person
    for person_result in person_results:
        if len(person_result.boxes) == 0:
            continue
        
        for person_box in person_result.boxes:
            person_conf = float(person_box.conf)
            if person_conf < CONFIDENCE_THRESHOLD:
                continue
            
            person_bbox = person_box.xyxy[0].cpu().numpy()
            px1, py1, px2, py2 = map(int, person_bbox)
            
            # Check if person is in ROI
            center_x = int((px1 + px2) / 2)
            center_y = int((py1 + py2) / 2)
            
            if camera_id in ROI_ZONES:
                if not is_point_in_polygon((center_x, center_y), ROI_ZONES[camera_id]):
                    continue
            
            if camera_id in NOT_DETECTED_ROI_ZONES:
                if is_point_in_polygon((center_x, center_y), NOT_DETECTED_ROI_ZONES[camera_id]):
                    continue
            
            # วาด person bbox (สีน้ำเงิน)
            # cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (255, 255, 0), 2)
            # cv2.putText(annotated_frame, f"Person {person_conf:.2f}", (px1, py1 - 10),
            #            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            # ⭐ STAGE 2: Detect PPE within person bbox
            ppe_detections = detect_ppe_in_person(frame, person_bbox)
            
            # ⭐ STAGE 3: Classify each PPE detection
            for ppe in ppe_detections:
                bbox = ppe['bbox']
                x1, y1, x2, y2 = bbox
                class_name = ppe['class']
                det_conf = ppe['conf']
                
                # Classify
                classified_name, class_conf, is_classified = classify_object(
                    frame, bbox, class_name
                )
                
                # Skip if classification failed
                if not is_classified or class_conf < CLASSIFICATION_THRESHOLD:
                    continue
                
                display_name = classified_name.split('_', 1)[1] if '_' in classified_name else classified_name
                
                # Check if NG or non-safety
                is_ng = classified_name.strip().upper() == "NG"
                is_non_safety = 'non-safety' in classified_name.lower()
                
                if is_ng or is_non_safety:
                    has_ng = True
                    ng_count_total[camera_id] += 1
                    alert_timestamp = time.time()
                    color = (0, 0, 255)  # Red
                elif 'safety' in classified_name.lower():
                    color = (0, 255, 0)  # Green
                else:
                    color = (255, 165, 0)  # Orange
                
                detections.append({
                    "class": class_name,
                    "classified_as": classified_name,
                    "detection_conf": round(det_conf, 2),
                    "classification_conf": round(class_conf, 2),
                    "bbox": bbox,
                    "person_bbox": [px1, py1, px2, py2]
                })
                
                # Draw PPE bbox
                thickness = 4 if (is_ng or is_non_safety) else 2
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
                
                # Draw label
                (label_w, label_h), _ = cv2.getTextSize(display_name, 
                                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated_frame,
                            (x1, y1 - label_h - 10),
                            (x1 + label_w + 10, y1),
                            color, -1)
                cv2.putText(annotated_frame, display_name, (x1 + 5, y1 - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.circle(annotated_frame, ((x1+x2)//2, (y1+y2)//2), 5, color, -1)
    
    return annotated_frame, detections, has_ng, alert_timestamp

# ---- CAMERA READER WITH DETECTION ----
def camera_reader_with_detection(index: int, url: str):
    cap = cv2.VideoCapture(url)
    
    # ⭐ Optimize capture settings
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 15)
    
    if not cap.isOpened():
        print(f"[Camera {index}] Cannot open: {url}")
        return
    
    print(f"[Camera {index}] Started streaming from {url}")
    frame_count = 0
    
    # ⭐ แต่ละกล้องเริ่ม offset คนละจุด
    detection_offset = index * CAMERA_OFFSET
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.1)
            continue
        
        # Store original frame
        with frame_locks[index]:
            latest_frames[index] = frame.copy()
        
        # ⭐ ตรวจจับเฉพาะทุก N เฟรม + offset ตามกล้อง
        if (frame_count + detection_offset) % DETECTION_INTERVAL == 0:
            if person_model is not None and model is not None:
                try:
                    # ⭐ ลด imgsz สำหรับ person detection
                    person_results = person_model(
                        frame,
                        device=DEVICE,
                        verbose=False,
                        half=USE_HALF_PRECISION,
                        imgsz=640  # ⭐ ลดจาก default
                    )
                    
                    annotated_frame, detections, has_ng, alert_timestamp = draw_detections_3stage(
                        frame, person_results, camera_id=index
                    )
                    
                    with frame_locks[index]:
                        detected_frames[index] = annotated_frame
                        detection_results[index] = detections
                        if alert_timestamp:
                            alert_timestamps[index] = alert_timestamp
                    
                    if has_ng:
                        save_ng_image(frame.copy(), annotated_frame.copy(), index, detections)
                        play_alert_sound(index)
                        
                except Exception as e:
                    print(f"[Camera {index}] Detection error: {e}")
                    with frame_locks[index]:
                        detected_frames[index] = frame.copy()
        else:
            # เฟรมที่ไม่ตรวจจับ ใช้ผลลัพธ์เก่า
            with frame_locks[index]:
                if detected_frames[index] is None:
                    detected_frames[index] = frame.copy()
        
        frame_count += 1
        time.sleep(0.01)
    
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
    print("🔌 Testing database connection...")
    if test_db_connection():
        print(f"📊 Database: {DB_CONFIG['database']} @ {DB_CONFIG['server']}")
    else:
        print("⚠️ Warning: Database connection failed - continuing without DB")
    
    print(f"NG Images Directory: {os.path.abspath(NG_SAVE_DIR)}")
    print(f"{'='*60}\n")
    
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
        "message": "CCTV Camera API with Two-Stage Detection (Detection + Classification)",
        "device": DEVICE,
        "detection_stages": {
            "stage_1": "Person Detection",
            "stage_2": "PPE Detection (hand, shoe, glasses, shirt)",
            "stage_3": "Safety Classification"
        },
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cameras": len(CAM_URLS),
        "person_model": PERSON_MODEL_PATH,
        "detection_model": MODEL_PATH,
        "classification_model": CLASSIFICATION_MODEL_PATH if ENABLE_CLASSIFICATION else None,
        "detection_loaded": model is not None,
        "classification_loaded": classification_model is not None,
        "detection_classes": model.names if model else {},
        "classification_classes": classification_model.names if classification_model else {},
        "class_mapping": CLASS_MAPPING,
        "enable_nms": ENABLE_NMS,
        "nms_iou_threshold": NMS_IOU_THRESHOLD,
        "classification_threshold": CLASSIFICATION_THRESHOLD,
        "ng_save_dir": NG_SAVE_DIR,
        "enable_tracking": ENABLE_TRACKING,
        "track_alert_cooldown": TRACK_ALERT_COOLDOWN,
        "email_alert_enabled": ENABLE_EMAIL_ALERT,
        "email_recipients": len(RECIPIENT_EMAILS) if ENABLE_EMAIL_ALERT else 0,
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

@app.get("/api/camera/{camera_id}/alert")
async def check_alert(camera_id: int):
    """Check if there's a recent alert for this camera"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    current_time = time.time()
    last_alert = alert_timestamps.get(camera_id, 0)
    
    # ถือว่า alert ยังใหม่ถ้าผ่านมาไม่เกิน 3 วินาที
    is_active = (current_time - last_alert) < 3
    
    return {
        "camera_id": camera_id,
        "has_alert": is_active,
        "last_alert_time": last_alert if last_alert > 0 else None
    }

# ---- EMAIL TEST ENDPOINTS ----
@app.get("/api/test/email")
async def test_email_simple():
    """ทดสอบส่งอีเมลแบบง่าย (ไม่มีรูปภาพ)"""
    if not ENABLE_EMAIL_ALERT:
        return {
            "success": False,
            "message": "Email alert is disabled in config"
        }
    
    try:
        msg = MIMEMultipart('related')
        msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg['To'] = ', '.join(RECIPIENT_EMAILS)
        msg['Cc'] = ', '.join(CC_EMAILS)  # ⭐ เพิ่ม CC
        msg['Subject'] = f"✅ Test Email - System Check [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px;">
                    <h2>✅ Email System Test</h2>
                </div>
                <div style="padding: 20px;">
                    <p>This is a test email from your CCTV Monitoring System.</p>
                    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>SMTP Server:</strong> {SMTP_SERVER}:{SMTP_PORT}</p>
                    <p><strong>Sender:</strong> {SENDER_EMAIL}</p>
                    <p><strong>TO Recipients:</strong> {len(RECIPIENT_EMAILS)}</p>
                    <ul>
                        {''.join([f'<li>{email}</li>' for email in RECIPIENT_EMAILS])}
                    </ul>
                    <p><strong>CC Recipients:</strong> {len(CC_EMAILS)}</p>
                    <ul>
                        {''.join([f'<li>{email}</li>' for email in CC_EMAILS])}
                    </ul>
                </div>
                <div style="background-color: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 5px;">
                    <p style="color: #666; font-size: 12px;">
                        If you received this email, your email configuration is working correctly! ✅
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # ⭐ รวม TO + CC
        all_recipients = RECIPIENT_EMAILS + CC_EMAILS
        
        print(f"📧 Testing email connection to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SENDER_PASSWORD:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())  # ⭐ ใช้ sendmail
        
        print(f"✅ Test email sent successfully!")
        return {
            "success": True,
            "message": "Test email sent successfully",
            "to_recipients": RECIPIENT_EMAILS,
            "cc_recipients": CC_EMAILS,  # ⭐ เพิ่ม
            "timestamp": datetime.now().isoformat()
        }
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return {
            "success": False,
            "error": "SMTP Authentication failed",
            "details": str(e),
            "suggestion": "Check your SENDER_EMAIL and SENDER_PASSWORD"
        }
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return {
            "success": False,
            "error": "Failed to send test email",
            "details": str(e)
        }

# ---- DATABASE TEST ENDPOINTS ----
@app.get("/api/db/test")
async def test_database():
    """ทดสอบการเชื่อมต่อ Database"""
    conn = get_db_connection()
    if not conn:
        return {
            "success": False,
            "message": "Cannot connect to database",
            "config": {
                "server": DB_CONFIG['server'],
                "database": DB_CONFIG['database'],
                "driver": DB_CONFIG['driver']
            }
        }
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        
        return {
            "success": True,
            "message": "Database connected successfully",
            "server_version": version,
            "config": {
                "server": DB_CONFIG['server'],
                "database": DB_CONFIG['database']
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

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
        if not full_path or full_path == "/":
            return FileResponse(static_path / "index.html")
        
        file_path = static_path / full_path
        
        if file_path.is_file():
            return FileResponse(file_path)
        
        html_path = static_path / f"{full_path}.html"
        if html_path.is_file():
            return FileResponse(html_path)
        
        index_path = static_path / full_path / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)
        
        return {"error": "Not found", "path": full_path}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)