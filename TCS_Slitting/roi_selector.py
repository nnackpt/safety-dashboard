import cv2
import json
import sys

CAM_URLS = [
    "rtsp://admin:@CCTV111@10.89.246.42:554/Streaming/Channels/101",
    "rtsp://admin:@CCTV111@10.89.246.43:554/Streaming/Channels/101",
]

# ---- GLOBAL VARIABLES ----
points = []
temp_point = None
show_instructions = True

def mouse_callback(event, x, y, flags, param):
    global points, temp_point
    
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"✓ Point {len(points)}: ({x}, {y})")
    
    elif event == cv2.EVENT_MOUSEMOVE:
        temp_point = (x, y)

def draw_roi_overlay(frame, points, temp_point=None):
    """Draw ROI points and lines on frame"""
    display = frame.copy()
    
    for i, point in enumerate(points):
        cv2.circle(display, point, 8, (0, 255, 0), -1)
        cv2.circle(display, point, 10, (255, 255, 255), 2)
        cv2.putText(display, str(i+1), (point[0]+15, point[1]-15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    if len(points) > 1:
        for i in range(len(points)):
            cv2.line(display, points[i], points[(i+1) % len(points)], 
                     (255, 255, 0), 3)
    
    if len(points) > 0 and temp_point:
        cv2.line(display, points[-1], temp_point, (100, 100, 255), 2)
    
    if len(points) >= 3:
        import numpy as np
        pts = np.array(points, np.int32)
        overlay = display.copy()
        cv2.fillPoly(overlay, [pts], (0, 255, 0))
        cv2.addWeighted(overlay, 0.3, display, 0.7, 0, display)
    
    return display

def select_roi_for_camera(camera_id):
    """Interactive ROI selection for a specific camera"""
    global points, temp_point, show_instructions
    points = []
    temp_point = None
    
    print(f"\n{'='*60}")
    print(f"📹 ROI Selection for Camera {camera_id + 1}")
    print(f"{'='*60}")
    print(f"URL: {CAM_URLS[camera_id]}")
    print("\nConnecting to camera...")
    
    cap = cv2.VideoCapture(CAM_URLS[camera_id])
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot connect to Camera {camera_id + 1}")
        return None
    
    print("✓ Connected successfully!")
    
    ret, frame = cap.read()
    if not ret or frame is None:
        print("❌ Error: Cannot read frame from camera")
        cap.release()
        return None
    
    print(f"✓ Frame size: {frame.shape[1]}x{frame.shape[0]}")
    print("\n" + "="*60)
    print("INSTRUCTIONS:")
    print("="*60)
    print("  • Click on the video to add points (minimum 3 points)")
    print("  • Points will connect to form a polygon")
    print("  • Press 's' to SAVE the ROI")
    print("  • Press 'r' to RESET and start over")
    print("  • Press 'u' to UNDO last point")
    print("  • Press 'q' to QUIT without saving")
    print("="*60 + "\n")
    
    window_name = f"ROI Selector - Camera {camera_id + 1}"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    cv2.setMouseCallback(window_name, mouse_callback)
    
    while True:
        display = draw_roi_overlay(frame, points, temp_point)
        
        if show_instructions:
            cv2.rectangle(display, (10, 10), (750, 130), (0, 0, 0), -1)
            cv2.rectangle(display, (10, 10), (750, 130), (255, 255, 255), 2)
            
            instructions = [
                f"Camera {camera_id + 1} - Points: {len(points)}",
                "'s'=Save | 'r'=Reset | 'u'=Undo | 'h'=Hide | 'q'=Quit",  # เพิ่ม 'h'=Hide
                f"Status: {'Ready to save ✓' if len(points) >= 3 else 'Add more points (min 3)'}"
            ]
            
            for i, text in enumerate(instructions):
                color = (0, 255, 0) if i == 2 and len(points) >= 3 else (255, 255, 255)
                cv2.putText(display, text, (20, 40 + i*30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow(window_name, display)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            if len(points) >= 3:
                print(f"\n✓ ROI saved with {len(points)} points")
                cv2.destroyAllWindows()
                cap.release()
                return points
            else:
                print(f"\n⚠ Warning: Need at least 3 points (current: {len(points)})")
        
        elif key == ord('r'):
            points = []
            temp_point = None
            print("\n↻ ROI reset")
        
        elif key == ord('u'):
            if len(points) > 0:
                removed = points.pop()
                print(f"\n↶ Undo: Removed point {removed}")
            else:
                print("\n⚠ No points to undo")
                
        elif key == ord('h'):
            show_instructions = not show_instructions
            status = "hidden" if not show_instructions else "shown"
            print(f"\n👁 Instructions {status}")
        
        elif key == ord('q'):
            print("\n✕ Quit without saving")
            cv2.destroyAllWindows()
            cap.release()
            return None
    
    cv2.destroyAllWindows()
    cap.release()
    return None

def main():
    print("\n" + "="*60)
    print("🎯 CCTV ROI (Region of Interest) Selector")
    print("="*60)
    print(f"Total cameras: {len(CAM_URLS)}\n")
    
    for i, url in enumerate(CAM_URLS):
        print(f"  Camera {i + 1}: {url}")
    
    print("\n" + "="*60)
    
    all_rois = {}
    
    for camera_id in range(len(CAM_URLS)):
        roi = select_roi_for_camera(camera_id)
        
        if roi is not None:
            all_rois[camera_id] = roi
            print(f"✓ Camera {camera_id + 1} ROI configured")
        else:
            print(f"✕ Camera {camera_id + 1} ROI skipped")
        
        if camera_id < len(CAM_URLS) - 1:
            print("\n" + "-"*60)
            response = input(f"\nContinue to Camera {camera_id + 2}? (y/n): ").strip().lower()
            if response != 'y':
                print("Stopping...")
                break
    
    if all_rois:
        filename = "roi_zones.json"
        with open(filename, 'w') as f:
            json.dump(all_rois, f, indent=2)
        
        print("\n" + "="*60)
        print("✓ SUCCESS: ROI configuration saved!")
        print("="*60)
        print(f"File: {filename}\n")
        
        print("Copy this to your main.py:")
        print("-"*60)
        print("ROI_ZONES = {")
        for cam_id, roi in all_rois.items():
            print(f"    {cam_id}: [")
            for point in roi:
                print(f"        {point},")
            print("    ],")
        print("}")
        print("-"*60)
        
    else:
        print("\n⚠ No ROI configurations saved")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✕ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)