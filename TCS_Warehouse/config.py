import os
import torch
import pytz
from pathlib import Path

# SYSTEM CONFIG
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
USE_HALF_PRECISION = True

print(f"🖥️  Device: {DEVICE}")
if DEVICE == 'cuda':
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 VRAM Available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# CAMERA CONFIG
CAM_URLS = [
    "rtsp://admin:@CCTV111@10.89.246.42:554/Streaming/Channels/101",
    "rtsp://admin:@CCTV111@10.89.246.43:554/Streaming/Channels/101",
]

# Display settings
DUAL_W, DUAL_H = 760, 720
SINGLE_W, SINGLE_H = 1024, 768

# OBSTACLE DETECTION ZONES
ROI_ZONES = {
    0: [
        (1712, 594),
        (1696, 664),
        (1671, 756),
        (1633, 845),
        (1595, 925),
        (1576, 965),
        (1523, 917),
        (1470, 897),
        (1410, 881),
        (1348, 886),
        (1283, 904),
        (1228, 948),
        (1191, 1011),
        (1187, 1053),
        (1192, 1071),
        (890, 1071),
        (592, 1074),
        (558, 914),
        (541, 771),
        (668, 638),
        (789, 522),
        (904, 414),
        (1021, 311),
        (1045, 288),
        (1239, 295),
        (1415, 311),
        (1537, 321),
        (1635, 330),
        (1559, 506),
        (1621, 543),
    ],
    1: [
        (230, 308),
        (414, 258),
        (374, 78),
        (592, 93),
        (798, 126),
        (949, 157),
        (985, 206),
        (1038, 278),
        (1127, 414),
        (1237, 589),
        (1328, 758),
        (1271, 889),
        (1213, 1011),
        (1180, 1074),
        (853, 1076),
        (568, 1063),
        (378, 1024),
        (321, 851),
        (283, 715),
        (258, 589),
        (239, 431),
    ],
}

DRAW_ROI = True
ROI_COLOR = (0, 0, 255)  # สีแดง
ROI_THICKNESS = 3

# Detection settings
DETECTION_INTERVAL = 10
CAMERA_OFFSET = 5

# MODEL CONFIG
MODEL_DIR = Path("Model")
PERSON_MODEL_PATH = MODEL_DIR / "person_forklift_train6.pt"
PPE_MODEL_PATH = MODEL_DIR / "object_train2.pt"
CLASSIFICATION_MODEL_PATH = MODEL_DIR / "classify_train1.pt"
OBSTACLE_MODEL_PATH = MODEL_DIR / "Obstruction.pt"
ENABLE_OBSTACLE_DETECTION = True

# Model thresholds
PERSON_CONFIDENCE_THRESHOLD = 0.5
PPE_CONFIDENCE_THRESHOLD = 0.5
CLASSIFICATION_THRESHOLD = 0.5
OBSTACLE_CONFIDENCE_THRESHOLD = 0.5

# NMS settings
ENABLE_NMS = True
NMS_IOU_THRESHOLD = 0.45

# CLASS MAPPING
PPE_CLASSES = {
    0: 'shirt',
    1: 'shoes',
    2: 'head',
}

CLASS_MAPPING = {
    'shirt': ['non-safety-vest', 'safety-vest'],
    'shoes': ['non-safety-shoes', 'safety-shoes'],
    'head': ['non-safety-helmet', 'safety-helmet'],
}

# NG IMAGE SAVING CONFIG
NG_SAVE_DIR = Path("ng_images_warehouse")
NG_COOLDOWN = 5  # วินาที
SAVE_ORIGINAL = True
SAVE_ANNOTATED = True
CONSECUTIVE_NG_THRESHOLD = 3

# Create directories
os.makedirs(NG_SAVE_DIR, exist_ok=True)
os.makedirs(NG_SAVE_DIR / "original", exist_ok=True)
os.makedirs(NG_SAVE_DIR / "annotated", exist_ok=True)
os.makedirs(NG_SAVE_DIR / "obstacle", exist_ok=True)

# SOUND ALERT CONFIG
ENABLE_SOUND_ALERT = True
SOUND_FILE = Path("Sound Alarm/emergency-alarmsiren-type.mp3")
SOUND_COOLDOWN = 10  # วินาที

# OBSTACLE ALERT SETTINGS
OBSTACLE_ALERT_THRESHOLD = 60  # วินาที ต้องเจอติดกัน 60 วิ
OBSTACLE_COOLDOWN_AFTER_ALERT = 300 # วินาที - ระยะเวลา cooldown หลัง alert
OBSTACLE_IS_NG = True
SAVE_OBSTACLE_IMAGES = True

# EMAIL ALERT CONFIG
ENABLE_EMAIL_ALERT = True
EMAIL_COOLDOWN = 300  # 5 นาที

# SMTP Settings
SMTP_SERVER = "smtp.alv.autoliv.int"
SMTP_PORT = 25
SENDER_EMAIL = "TCS-PPE-Safety@autoliv.com"
SENDER_PASSWORD = ""
SENDER_NAME = "PPE-Safety Alert"

RECIPIENT_EMAILS = [
    "phakin.thongla-ar.external@autoliv.com",
    "kuntika.prasitnawa.external@autoliv.com",
    "rutthaya.larot@autoliv.com"
]

CC_EMAILS = [
    "panitsada.siritianwanitchakun@autoliv.com",
    "kittisak.wongprachanukul@autoliv.com",
]

# TIMEZONE CONFIG
TH = pytz.timezone('Asia/Bangkok')

# API CONFIG
API_PORT = 8084
API_HOST = "0.0.0.0"
API_TITLE = "Warehouse PPE Detection API"