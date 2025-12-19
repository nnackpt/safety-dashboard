import os
import time
import cv2
import threading
import pygame
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
from datetime import datetime
from config import (
    ENABLE_SOUND_ALERT, SOUND_FILE, SOUND_COOLDOWN,
    ENABLE_EMAIL_ALERT, EMAIL_COOLDOWN,
    SMTP_SERVER, SMTP_PORT,
    SENDER_EMAIL, SENDER_PASSWORD, SENDER_NAME,
    RECIPIENT_EMAILS, CC_EMAILS,
    NG_SAVE_DIR, SAVE_ORIGINAL, SAVE_ANNOTATED,
    TH,
    OBSTACLE_ALERT_THRESHOLD, SAVE_OBSTACLE_IMAGES
)


# SOUND ALERT
class SoundAlert:
    """Manages sound alert system"""
    
    def __init__(self):
        self.alert_sound = None
        self.last_sound_time = {}
        self.sound_lock = threading.Lock()
        
        if ENABLE_SOUND_ALERT:
            self._init_sound()
    
    def _init_sound(self):
        """Initialize pygame mixer and load sound"""
        try:
            pygame.mixer.init()
            if os.path.exists(SOUND_FILE):
                self.alert_sound = pygame.mixer.Sound(str(SOUND_FILE))
                print(f"✅ Sound alert loaded: {SOUND_FILE}")
            else:
                self.alert_sound = None
                print(f"⚠️ Sound file not found: {SOUND_FILE}")
        except Exception as e:
            self.alert_sound = None
            print(f"❌ Error loading sound: {e}")
    
    def play(self, camera_id):
        if not ENABLE_SOUND_ALERT or self.alert_sound is None:
            return False
        
        try:
            current_time = time.time()
            
            with self.sound_lock:
                last_time = self.last_sound_time.get(camera_id, 0)
                if current_time - last_time < SOUND_COOLDOWN:
                    return False
                self.last_sound_time[camera_id] = current_time
            
            # Play sound (non-blocking)
            self.alert_sound.play()
            print(f"🔔 [Camera {camera_id+1}] Alert sound played")
            return True
            
        except Exception as e:
            print(f"❌ Error playing sound: {e}")
            return False


# EMAIL ALERT
class EmailAlert:
    """Manages email alert system"""
    
    def __init__(self):
        self.last_email_time = {}
        self.email_lock = threading.Lock()
    
    def send_alert(self, camera_id, ng_count, image_paths, ng_detections):
        if not ENABLE_EMAIL_ALERT:
            return False
        
        try:
            current_time = time.time()
            
            # Check cooldown
            with self.email_lock:
                last_time = self.last_email_time.get(camera_id, 0)
                if current_time - last_time < EMAIL_COOLDOWN:
                    print(f"⏳ [Camera {camera_id+1}] Email cooldown active, skipping...")
                    return False
                self.last_email_time[camera_id] = current_time
            
            # Group detections by type
            detection_summary = {}
            for d in ng_detections:
                classified_as = d.get('classified_as', 'unknown')
                display_name = classified_as.replace('-', ' ').title()
                
                if display_name not in detection_summary:
                    detection_summary[display_name] = 0
                detection_summary[display_name] += 1
            
            # Create detection table HTML
            detection_html = ""
            for class_name, count in detection_summary.items():
                detection_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #ffe6e6;">
                        <span style="color: #ff0000; font-weight: bold;">⚠️ {class_name}</span>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #ff0000;">
                        {count}
                    </td>
                </tr>
                """
            
            # Create email message
            msg = MIMEMultipart('related')
            msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
            msg['To'] = ', '.join(RECIPIENT_EMAILS)
            msg['Cc'] = ', '.join(CC_EMAILS)
            msg['Subject'] = f"⚠️ Warehouse PPE NG Detected - Camera {camera_id+1} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
            
            # Create HTML body
            annotated_path = image_paths.get('annotated')
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="background-color: #ff0000; color: white; padding: 20px; border-radius: 5px;">
                        <h2>🚨 Warehouse PPE NG Detection Alert</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p><strong>Camera:</strong> Camera {camera_id+1}</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Total NG/Non-Safety Count:</strong> <span style="color: red; font-size: 24px; font-weight: bold;">{ng_count}</span></p>
                        <p><strong>Location:</strong> Warehouse Area</p>
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
                            This is an automated alert from Warehouse PPE Monitoring System.<br>
                            Please check the cameras immediately and ensure proper PPE usage.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach inline image
            if annotated_path and os.path.exists(annotated_path):
                with open(annotated_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-ID', '<detection_image>')
                    image.add_header('Content-Disposition', 'inline', filename=os.path.basename(annotated_path))
                    msg.attach(image)
                
                print(f"📎 [Camera {camera_id+1}] Attached inline image: {os.path.basename(annotated_path)}")
            
            all_recipients = RECIPIENT_EMAILS + CC_EMAILS
            
            # Send email
            print(f"📧 [Camera {camera_id+1}] Connecting to SMTP server...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                if SENDER_PASSWORD:
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            
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

    def send_obstacle_alert(self, camera_id, obstacle_count, image_paths, obstacle_detections, duration):
        """
        Send email alert for obstacle detection
        
        Args:
            camera_id: Camera ID
            obstacle_count: Number of obstacles detected
            image_paths: Dict with 'original' and 'annotated' paths
            obstacle_detections: List of obstacle detection details
            duration: Duration of obstacle presence (seconds)
            
        Returns:
            bool: True if email sent successfully
        """
        if not ENABLE_EMAIL_ALERT:
            return False
        
        try:
            current_time = time.time()
            
            with self.email_lock:
                last_time = self.last_email_time.get(camera_id, 0)
                if current_time - last_time < EMAIL_COOLDOWN:
                    print(f"⏳ [Camera {camera_id+1}] Email cooldown active, skipping...")
                    return False
                self.last_email_time[camera_id] = current_time
            
            # Group detections by obstacle class
            detection_summary = {}
            for d in obstacle_detections:
                class_name = d.get('class', 'unknown')
                display_name = class_name.replace('-', ' ').replace('_', ' ').title()
                
                if display_name not in detection_summary:
                    detection_summary[display_name] = 0
                detection_summary[display_name] += 1
            
            # Create detection table HTML
            detection_html = ""
            for class_name, count in detection_summary.items():
                detection_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #fff3e0;">
                        <span style="color: #ff6f00; font-weight: bold;">⚠️ {class_name}</span>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: #ff6f00;">
                        {count}
                    </td>
                </tr>
                """
            
            # Format duration
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            
            # Create email message
            msg = MIMEMultipart('related')
            msg['From'] = formataddr((SENDER_NAME, SENDER_EMAIL))
            msg['To'] = ', '.join(RECIPIENT_EMAILS)
            msg['Cc'] = ', '.join(CC_EMAILS)
            msg['Subject'] = f"🚨 Obstacle Alert - Camera {camera_id+1} - Duration: {duration_str} [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
            
            # Create HTML body
            annotated_path = image_paths.get('annotated')
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="background-color: #ff6f00; color: white; padding: 20px; border-radius: 5px;">
                        <h2>🚨 Warehouse Obstacle Alert</h2>
                    </div>
                    <div style="padding: 20px;">
                        <p><strong>Camera:</strong> Camera {camera_id+1}</p>
                        <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Alert Type:</strong> <span style="color: #ff6f00; font-size: 18px; font-weight: bold;">OBSTACLE IN ROI ZONE</span></p>
                        <p><strong>Duration:</strong> <span style="color: #ff6f00; font-size: 24px; font-weight: bold;">{duration_str}</span> (Threshold: {OBSTACLE_ALERT_THRESHOLD}s)</p>
                        <p><strong>Total Obstacles:</strong> <span style="color: #ff6f00; font-size: 24px; font-weight: bold;">{obstacle_count}</span></p>
                        <p><strong>Location:</strong> Warehouse Area - ROI Zone</p>
                    </div>
                    
                    <div style="padding: 20px;">
                        <h3>📋 Obstacle Details:</h3>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                            <thead>
                                <tr style="background-color: #f0f0f0;">
                                    <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Obstacle Type</th>
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
                html_body += '<img src="cid:detection_image" style="max-width: 800px; width: 100%; border: 3px solid #ff6f00; margin: 10px 0; display: block;"><br>'
            else:
                html_body += '<p style="color: #ff6f00;">⚠️ No detection image available</p>'
            
            html_body += """
                    </div>
                    <div style="background-color: #fff3e0; padding: 15px; margin-top: 20px; border-radius: 5px; border-left: 4px solid #ff6f00;">
                        <p style="color: #ff6f00; font-size: 14px; font-weight: bold; margin: 0 0 10px 0;">
                            ⚠️ ACTION REQUIRED
                        </p>
                        <p style="color: #666; font-size: 12px; margin: 0;">
                            An obstacle has been detected in the ROI zone for more than the threshold duration.<br>
                            Please check the warehouse area immediately and clear the obstacle to prevent operational disruptions.<br>
                            <br>
                            This is an automated alert from Warehouse PPE Monitoring System.
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach inline image
            if annotated_path and os.path.exists(annotated_path):
                with open(annotated_path, 'rb') as f:
                    img_data = f.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-ID', '<detection_image>')
                    image.add_header('Content-Disposition', 'inline', filename=os.path.basename(annotated_path))
                    msg.attach(image)
                
                print(f"📎 [Camera {camera_id+1}] Attached inline image: {os.path.basename(annotated_path)}")
            
            all_recipients = RECIPIENT_EMAILS + CC_EMAILS
            
            # Send email
            print(f"📧 [Camera {camera_id+1}] Sending obstacle alert email...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                if SENDER_PASSWORD:
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            
            print(f"✅ [Camera {camera_id+1}] Obstacle alert email sent!")
            print(f"   Duration: {duration_str}")
            print(f"   Obstacle types:")
            for class_name, count in detection_summary.items():
                print(f"   - {class_name}: {count}")
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"❌ Email authentication failed. Check your email/password")
            return False
        except Exception as e:
            print(f"❌ Error sending obstacle alert email: {e}")
            return False

# NG IMAGE SAVING
def save_ng_image(original_frame, annotated_frame, camera_id, detections):
    try:
        timestamp = datetime.now(TH).strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # Filter NG detections only
        ng_detections = [d for d in detections if d.get('is_ng', False)]
        ng_count = len(ng_detections)
        
        base_filename = f"cam{camera_id+1}_ng{ng_count}_{timestamp}"
        
        image_paths = {}
        
        # Save original
        if SAVE_ORIGINAL:
            original_path = NG_SAVE_DIR / "original" / f"{base_filename}_orig.jpg"
            cv2.imwrite(str(original_path), original_frame)
            image_paths['original'] = str(original_path)
        
        # Save annotated
        if SAVE_ANNOTATED:
            annotated_path = NG_SAVE_DIR / "annotated" / f"{base_filename}_anno.jpg"
            info_frame = annotated_frame.copy()
            
            # Add info overlay
            cv2.rectangle(info_frame, (10, 10), (600, 120), (0, 0, 0), -1)
            cv2.rectangle(info_frame, (10, 10), (600, 120), (0, 0, 255), 3)
            cv2.putText(info_frame, f"NG DETECTED - Camera {camera_id+1}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(info_frame, f"Time: {datetime.now(TH).strftime('%Y-%m-%d %H:%M:%S')}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(info_frame, f"NG Count: {ng_count}", (20, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imwrite(str(annotated_path), info_frame)
            image_paths['annotated'] = str(annotated_path)
        
        print(f"📸 [Camera {camera_id+1}] NG image saved: {base_filename}")
        return image_paths, ng_detections
        
    except Exception as e:
        print(f"❌ Error saving NG image: {e}")
        return {}, []


# OBSTACLE IMAGE SAVING
def save_obstacle_image(original_frame, annotated_frame, camera_id, detections, duration):
    """
    Save obstacle detection images
    
    Args:
        original_frame: Original camera frame
        annotated_frame: Annotated frame with detections
        camera_id: Camera ID
        detections: List of detections
        duration: Duration of obstacle presence (seconds)
        
    Returns:
        tuple: (image_paths dict, obstacle_detections list)
    """
    if not SAVE_OBSTACLE_IMAGES:
        return {}, []
    
    try:
        timestamp = datetime.now(TH).strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # Filter obstacle detections only
        obstacle_detections = [d for d in detections if d.get('type') == 'obstacle']
        obstacle_count = len(obstacle_detections)
        
        # Create filename with duration
        base_filename = f"cam{camera_id+1}_obstacle{obstacle_count}_dur{int(duration)}s_{timestamp}"
        
        image_paths = {}
        
        # Save original
        if SAVE_ORIGINAL:
            original_path = NG_SAVE_DIR / "original" / f"{base_filename}_orig.jpg"
            cv2.imwrite(str(original_path), original_frame)
            image_paths['original'] = str(original_path)
        
        # Save annotated with info overlay
        if SAVE_ANNOTATED:
            annotated_path = NG_SAVE_DIR / "annotated" / f"{base_filename}_anno.jpg"
            info_frame = annotated_frame.copy()
            
            # Add info overlay
            cv2.rectangle(info_frame, (10, 10), (700, 140), (0, 0, 0), -1)
            cv2.rectangle(info_frame, (10, 10), (700, 140), (0, 165, 255), 3)  # สีส้ม
            
            cv2.putText(info_frame, f"OBSTACLE ALERT - Camera {camera_id+1}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(info_frame, f"Time: {datetime.now(TH).strftime('%Y-%m-%d %H:%M:%S')}", (20, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(info_frame, f"Obstacle Count: {obstacle_count}", (20, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.putText(info_frame, f"Duration: {duration:.1f}s (Threshold: {OBSTACLE_ALERT_THRESHOLD}s)", (20, 130),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            
            cv2.imwrite(str(annotated_path), info_frame)
            image_paths['annotated'] = str(annotated_path)
        
        print(f"📸 [Camera {camera_id+1}] Obstacle image saved: {base_filename}")
        return image_paths, obstacle_detections
        
    except Exception as e:
        print(f"❌ Error saving obstacle image: {e}")
        return {}, []
    
    
# Global instances
sound_alert = SoundAlert()
email_alert = EmailAlert()

__all__ = ['sound_alert', 'email_alert', 'save_ng_image', 'save_obstacle_image']