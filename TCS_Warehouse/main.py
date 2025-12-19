from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import cv2
import time
import os
from pathlib import Path
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from config import (
    API_HOST, API_PORT, API_TITLE,
    CAM_URLS, DUAL_W, DUAL_H, SINGLE_W, SINGLE_H,
    NG_SAVE_DIR,
    ENABLE_EMAIL_ALERT, RECIPIENT_EMAILS, CC_EMAILS,
    SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, SENDER_NAME
)
from models import model_manager
from camera_manager import camera_manager


# FASTAPI APP SETUP
app = FastAPI(title=API_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# STARTUP/SHUTDOWN EVENTS
@app.on_event("startup")
async def startup_event():
    """Initialize and start camera system"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Warehouse PPE Detection System")
    print(f"{'='*60}")
    
    # Check if models are ready
    if not model_manager.is_ready():
        print("❌ Models not loaded properly!")
        return
    
    # Start cameras
    camera_manager.start()
    
    print(f"✅ System ready on port {API_PORT}")
    print(f"{'='*60}\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop camera system"""
    camera_manager.stop()


# API ENDPOINTS
@app.get("/api")
async def root():
    """API information"""
    from config import OBSTACLE_ALERT_THRESHOLD
    
    return {
        "name": API_TITLE,
        "version": "1.0.0",
        "status": "running",
        "models": {
            "person_detection": model_manager.person_model is not None,
            "ppe_detection": model_manager.ppe_model is not None,
            "classification": model_manager.classification_model is not None,
            "obstacle_detection": model_manager.obstacle_model is not None
        },
        "cameras": len(CAM_URLS),
        "obstacle_alert_threshold": OBSTACLE_ALERT_THRESHOLD,
        "endpoints": [
            "GET /api - API info",
            "GET /cameras - List all cameras",
            "GET /camera/{id} - Camera info",
            "GET /camera/{id}/stream - Original video stream",
            "GET /camera/{id}/stream/detected - Detected video stream",
            "GET /camera/{id}/detections - Current detections",
            "GET /camera/{id}/snapshot - Single frame",
            "GET /camera/{id}/alert - Check alert status",
            "GET /camera/{id}/obstacle - Check obstacle status with timing",
            "GET /obstacles/status - All cameras obstacle status",
            "GET /statistics - Detection statistics",
            "GET /ng-images - List saved NG images",
            "GET /test/email - Test email alert"
        ]
    }


@app.get("/cameras")
async def get_cameras():
    """Get list of all cameras with status"""
    cameras = []
    for i in range(len(CAM_URLS)):
        frame = camera_manager.get_latest_frame(i)
        detections = camera_manager.get_detections(i)
        stats = camera_manager.get_statistics(i)
        
        cameras.append({
            "id": i,
            "url": CAM_URLS[i],
            "status": "active" if frame is not None else "inactive",
            "detections": len(detections),
            "ng_detected": stats["total_ng_detected"],
            "ng_saved": stats["images_saved"]
        })
    
    return {"cameras": cameras}


@app.get("/camera/{camera_id}")
async def get_camera_info(camera_id: int):
    """Get specific camera information"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    frame = camera_manager.get_latest_frame(camera_id)
    detections = camera_manager.get_detections(camera_id)
    stats = camera_manager.get_statistics(camera_id)
    
    height, width = frame.shape[:2] if frame is not None else (0, 0)
    
    return {
        "id": camera_id,
        "url": CAM_URLS[camera_id],
        "status": "active" if frame is not None else "inactive",
        "resolution": f"{width}x{height}",
        "detections": len(detections),
        "ng_detected": stats["total_ng_detected"],
        "ng_saved": stats["images_saved"]
    }


@app.get("/camera/{camera_id}/stream")
async def video_stream(camera_id: int, single: bool = False):
    """Stream original video (MJPEG)"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    target_w = SINGLE_W if single else DUAL_W
    target_h = SINGLE_H if single else DUAL_H
    
    def generate():
        while True:
            frame = camera_manager.get_latest_frame(camera_id)
            
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


@app.get("/camera/{camera_id}/stream/detected")
async def video_stream_detected(camera_id: int, single: bool = False):
    """Stream video with detections (MJPEG)"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    target_w = SINGLE_W if single else DUAL_W
    target_h = SINGLE_H if single else DUAL_H
    
    def generate():
        while True:
            frame = camera_manager.get_detected_frame(camera_id)
            
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


@app.get("/camera/{camera_id}/snapshot")
async def get_snapshot(camera_id: int, detected: bool = False, single: bool = False):
    """Get single frame as JPEG"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    frame = camera_manager.get_detected_frame(camera_id) if detected else camera_manager.get_latest_frame(camera_id)
    
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


@app.get("/camera/{camera_id}/detections")
async def get_detections(camera_id: int):
    """Get current detections for camera"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    detections = camera_manager.get_detections(camera_id)
    
    # Count NG detections
    ng_count = sum(1 for d in detections if d.get('is_ng', False))
    obstacle_count = sum(1 for d in detections if d.get('type') == 'obstacle')
    
    return {
        "camera_id": camera_id,
        "count": len(detections),
        "ng_count": ng_count,
        "obstacle_count": obstacle_count,
        "detections": detections
    }


@app.get("/camera/{camera_id}/alert")
async def check_alert(camera_id: int):
    """Check if there's a recent alert"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    has_alert = camera_manager.has_recent_alert(camera_id, threshold_seconds=3)
    
    return {
        "camera_id": camera_id,
        "has_alert": has_alert
    }


@app.get("/camera/{camera_id}/obstacle")
async def check_obstacle(camera_id: int):
    """Check obstacle detection status with duration"""
    if camera_id < 0 or camera_id >= len(CAM_URLS):
        return {"error": "Invalid camera ID"}
    
    has_obstacle = camera_manager.has_recent_obstacle(camera_id)
    current_duration = camera_manager.get_obstacle_duration(camera_id)
    
    from config import OBSTACLE_ALERT_THRESHOLD
    
    return {
        "camera_id": camera_id,
        "has_obstacle": has_obstacle,
        "current_duration": round(current_duration, 1),
        "alert_threshold": OBSTACLE_ALERT_THRESHOLD,
        "alert_triggered": has_obstacle,
        "time_remaining": max(0, round(OBSTACLE_ALERT_THRESHOLD - current_duration, 1)) if current_duration > 0 else 0,
        "total_obstacles": camera_manager.obstacle_count_total[camera_id]
    }
    
@app.get("/obstacles/status")
async def get_all_obstacles_status():
    """Get obstacle detection status for all cameras"""
    from config import OBSTACLE_ALERT_THRESHOLD
    
    statuses = []
    for i in range(len(CAM_URLS)):
        current_duration = camera_manager.get_obstacle_duration(i)
        has_obstacle = camera_manager.has_recent_obstacle(i)
        
        statuses.append({
            "camera_id": i,
            "has_obstacle": current_duration > 0,
            "current_duration": round(current_duration, 1),
            "alert_triggered": has_obstacle,
            "time_remaining": max(0, round(OBSTACLE_ALERT_THRESHOLD - current_duration, 1)) if current_duration > 0 else 0,
            "total_alerts": camera_manager.obstacle_count_total[i]
        })
    
    return {
        "alert_threshold": OBSTACLE_ALERT_THRESHOLD,
        "cameras": statuses
    }

@app.get("/statistics")
async def get_statistics():
    """Get detection statistics"""
    stats = camera_manager.get_statistics()
    
    return {
        **stats,
        "save_directory": str(NG_SAVE_DIR.absolute())
    }


@app.get("/ng-images")
async def list_ng_images():
    """List all saved NG images"""
    images = {
        "original": [],
        "annotated": []
    }
    
    # List original images
    original_dir = NG_SAVE_DIR / "original"
    if original_dir.exists():
        for filename in sorted(os.listdir(original_dir), reverse=True):
            if filename.endswith(('.jpg', '.png')):
                file_path = original_dir / filename
                file_stat = os.stat(file_path)
                images["original"].append({
                    "filename": filename,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })
    
    # List annotated images
    annotated_dir = NG_SAVE_DIR / "annotated"
    if annotated_dir.exists():
        for filename in sorted(os.listdir(annotated_dir), reverse=True):
            if filename.endswith(('.jpg', '.png')):
                file_path = annotated_dir / filename
                file_stat = os.stat(file_path)
                images["annotated"].append({
                    "filename": filename,
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })
    
    return {
        "total_images": len(images["original"]) + len(images["annotated"]),
        "images": images
    }


@app.get("/test/email")
async def test_email():
    """Test email alert system"""
    if not ENABLE_EMAIL_ALERT:
        return {
            "success": False,
            "message": "Email alert is disabled in config"
        }
    
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
        msg['To'] = ', '.join(RECIPIENT_EMAILS)
        msg['Cc'] = ', '.join(CC_EMAILS)
        msg['Subject'] = f"✅ Test Email - Warehouse PPE System [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px;">
                    <h2>✅ Warehouse PPE Email System Test</h2>
                </div>
                <div style="padding: 20px;">
                    <p>This is a test email from Warehouse PPE Monitoring System.</p>
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
        
        all_recipients = RECIPIENT_EMAILS + CC_EMAILS
        
        print(f"📧 Testing email connection to {SMTP_SERVER}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SENDER_PASSWORD:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
        
        print(f"✅ Test email sent successfully!")
        return {
            "success": True,
            "message": "Test email sent successfully",
            "to_recipients": RECIPIENT_EMAILS,
            "cc_recipients": CC_EMAILS,
            "timestamp": datetime.now().isoformat()
        }
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return {
            "success": False,
            "error": "SMTP Authentication failed",
            "details": str(e)
        }
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return {
            "success": False,
            "error": "Failed to send test email",
            "details": str(e)
        }

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

# MAIN
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)