from fastapi import APIRouter
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path
import cv2
import time
import os
from datetime import datetime
from config import *

router = APIRouter()

# Import global state variables from main module
def get_global_state():
    import main
    return (
        main.latest_frames,
        main.detected_frames,
        main.detection_results,
        main.frame_locks,
        main.ng_count_total,
        main.ng_saved_count,
        main.model
    )

@router.get("/api")
async def root():
    """API info"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/cameras")
async def get_cameras():
    """Get list of all cameras with status"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/camera/{camera_id}")
async def get_camera_info(camera_id: int):
    """Get specific camera information"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/camera/{camera_id}/detections")
async def get_detections(camera_id: int):
    """Get current detections for a camera"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    with frame_locks[camera_id]:
        detections = detection_results[camera_id].copy()
    
    ng_count = sum(1 for d in detections if d['class'].strip().upper() == 'NG')
    
    return {
        "camera_id": camera_id,
        "count": len(detections),
        "ng_count": ng_count,
        "detections": detections
    }

@router.get("/api/statistics")
async def get_statistics():
    """Get NG detection statistics"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/ng-images")
async def list_ng_images():
    """List all saved NG images"""
    images = {
        "original": [],
        "annotated": []
    }
    
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

@router.get("/api/camera/{camera_id}/stream")
async def video_stream(camera_id: int, single: bool = False):
    """Stream original video from specific camera (MJPEG)"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/camera/{camera_id}/stream/detected")
async def video_stream_detected(camera_id: int, single: bool = False):
    """Stream video with object detection overlays (MJPEG)"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

@router.get("/api/camera/{camera_id}/snapshot")
async def get_snapshot(camera_id: int, detected: bool = False, single: bool = False):
    """Get single frame as JPEG image"""
    latest_frames, detected_frames, detection_results, frame_locks, ng_count_total, ng_saved_count, model = get_global_state()
    
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

def create_static_routes():
    """Create static file routes"""
    static_routes = []
    
    static_path = Path("./out")
    if static_path.exists():
        for item in static_path.glob("*.png"):
            @router.get(f"/{item.name}")
            async def serve_static_png(filename: str = item.name):
                return FileResponse(static_path / filename)
        
        for item in static_path.glob("*.jpg"):
            @router.get(f"/{item.name}")
            async def serve_static_jpg(filename: str = item.name):
                return FileResponse(static_path / filename)
        
        @router.get("/{full_path:path}")
        async def serve_nextjs(full_path: str):
            file_path = static_path / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            
            html_path = static_path / f"{full_path}.html"
            if html_path.is_file():
                return FileResponse(html_path)
            
            return FileResponse(static_path / "index.html")
    
    return static_routes

create_static_routes()