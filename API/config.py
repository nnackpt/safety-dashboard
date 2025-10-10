import os
from typing import Dict, List, Tuple

# ---- CAMERA CONFIG ----
CAM_URLS = [
    "rtsp://admin:@CCTV111@10.89.246.38:554/Streaming/Channels/101",
    "rtsp://admin:@CCTV111@10.89.246.31:554/Streaming/Channels/101",
]

# ---- ROI ZONES CONFIG ----
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

# ---- DISPLAY CONFIG ----
DRAW_ROI = True
DRAW_EXCLUSION_ZONE = True

DUAL_W, DUAL_H = 760, 720
SINGLE_W, SINGLE_H = 1920, 1080

# ---- MODEL CONFIG ----
MODEL_PATH = "best.pt"
CONFIDENCE_THRESHOLD = 0.5

# ---- NG IMAGE SAVING CONFIG ----
NG_SAVE_DIR = "ng_images"
NG_COOLDOWN = 5
SAVE_ORIGINAL = True
SAVE_ANNOTATED = True

# ---- SOUND ALERT CONFIG ----
ENABLE_SOUND_ALERT = True
SOUND_FILE = r"Sound Alarm\level-up-07-383747.mp3"
SOUND_COOLDOWN = 5

# ---- API CONFIG ----
API_HOST = "0.0.0.0"
API_PORT = 8083

# Create required directories
os.makedirs(NG_SAVE_DIR, exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "original"), exist_ok=True)
os.makedirs(os.path.join(NG_SAVE_DIR, "annotated"), exist_ok=True)