"""
3-Stage PPE Detection Logic:
Stage 1: Person Detection
Stage 2: PPE Detection within person bbox
Stage 3: Safety Classification
"""
import cv2
import numpy as np
import torch
from config import (
    PERSON_CONFIDENCE_THRESHOLD,
    PPE_CONFIDENCE_THRESHOLD,
    CLASSIFICATION_THRESHOLD,
    CLASS_MAPPING,
    ENABLE_NMS,
    NMS_IOU_THRESHOLD,
    ROI_ZONES, DRAW_ROI, ROI_COLOR, ROI_THICKNESS,
    ENABLE_OBSTACLE_DETECTION, OBSTACLE_CONFIDENCE_THRESHOLD
)
from models import model_manager


def apply_nms(boxes, scores, iou_threshold=0.45):
    """
    Apply Non-Maximum Suppression to filter overlapping boxes
    
    Args:
        boxes: Tensor of bounding boxes [N, 4]
        scores: Tensor of confidence scores [N]
        iou_threshold: IoU threshold for NMS
        
    Returns:
        Tensor of indices to keep
    """
    if len(boxes) == 0:
        return torch.tensor([])
    
    keep = torch.ops.torchvision.nms(boxes, scores, iou_threshold)
    return keep


def crop_bbox(image, bbox, padding=10):
    """
    Crop region from image with optional padding
    
    Args:
        image: Input image
        bbox: Bounding box [x1, y1, x2, y2]
        padding: Padding around bbox
        
    Returns:
        Cropped image
    """
    x1, y1, x2, y2 = map(int, bbox)
    
    # Add padding
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(image.shape[1], x2 + padding)
    y2 = min(image.shape[0], y2 + padding)
    
    cropped = image[y1:y2, x1:x2]
    return cropped


def classify_ppe_item(frame, bbox, detected_class):
    """
    Stage 3: Classify PPE item as safety or non-safety
    
    Args:
        frame: Original frame
        bbox: Bounding box of PPE item
        detected_class: Detected class name (shirt/shoes/head)
        
    Returns:
        tuple: (classified_name, confidence, is_classified)
    """
    # Check if this class needs classification
    if detected_class not in CLASS_MAPPING:
        return detected_class, 0.0, False
    
    try:
        # Crop PPE item
        cropped = crop_bbox(frame, bbox, padding=10)
        
        if cropped.size == 0:
            print(f"⚠️ Empty crop for {detected_class}")
            return detected_class, 0.0, False
        
        # Run classification
        class_name, confidence = model_manager.classify_ppe(cropped)
        
        if class_name is None:
            return detected_class, 0.0, False
        
        # Validate that classification result is in expected classes
        relevant_classes = CLASS_MAPPING.get(detected_class, [])
        
        if class_name in relevant_classes:
            print(f"✅ Classified {detected_class} → {class_name} (conf: {confidence:.2f})")
            return class_name, confidence, True
        else:
            print(f"⚠️ Unexpected class {class_name} for {detected_class}")
            return detected_class, 0.0, False
        
    except Exception as e:
        print(f"❌ Classification error for {detected_class}: {e}")
        return detected_class, 0.0, False


def detect_ppe_in_person(frame, person_bbox):
    """
    Stage 2: Detect PPE items within person bounding box
    
    Args:
        frame: Original frame
        person_bbox: Person bounding box [x1, y1, x2, y2]
        
    Returns:
        list: List of PPE detections with adjusted coordinates
    """
    try:
        # Crop person region with padding
        person_crop = crop_bbox(frame, person_bbox, padding=20)
        
        if person_crop.size == 0:
            return []
        
        # Run PPE detection on cropped image
        ppe_results = model_manager.detect_ppe(
            person_crop,
            conf_threshold=PPE_CONFIDENCE_THRESHOLD
        )
        
        if ppe_results is None or len(ppe_results[0].boxes) == 0:
            return []
        
        # Get detection results
        boxes = ppe_results[0].boxes.xyxy
        scores = ppe_results[0].boxes.conf
        classes = ppe_results[0].boxes.cls
        
        # Apply NMS if enabled
        if ENABLE_NMS and len(boxes) > 1:
            keep = apply_nms(boxes, scores, iou_threshold=NMS_IOU_THRESHOLD)
            boxes = boxes[keep]
            scores = scores[keep]
            classes = classes[keep]
        
        # Convert to original frame coordinates
        detections = []
        x1_offset, y1_offset = map(int, person_bbox[:2])
        
        for i in range(len(boxes)):
            crop_x1, crop_y1, crop_x2, crop_y2 = boxes[i].cpu().numpy()
            
            # Convert to original frame coordinates
            orig_x1 = int(crop_x1 + x1_offset)
            orig_y1 = int(crop_y1 + y1_offset)
            orig_x2 = int(crop_x2 + x1_offset)
            orig_y2 = int(crop_y2 + y1_offset)
            
            cls_id = int(classes[i])
            class_name = model_manager.ppe_model.names[cls_id]
            conf = float(scores[i])
            
            detections.append({
                'bbox': [orig_x1, orig_y1, orig_x2, orig_y2],
                'conf': conf,
                'class': class_name,
                'cls': cls_id
            })
        
        return detections
        
    except Exception as e:
        print(f"❌ Error in detect_ppe_in_person: {e}")
        return []


def detect_and_classify(frame, camera_id=0):
    """
    Main detection function: 3-Stage Detection
    Stage 1: Person Detection
    Stage 2: PPE Detection
    Stage 3: Safety Classification
    
    Args:
        frame: Input frame
        
    Returns:
        tuple: (annotated_frame, detections, has_ng)
    """
    annotated_frame = frame.copy()
    all_detections = []
    has_ng = False
    has_obstacle = False
    
    if DRAW_ROI and camera_id in ROI_ZONES:
        roi = ROI_ZONES[camera_id]
        pts = np.array(roi, np.int32).reshape((-1, 1, 2))
        cv2.polylines(annotated_frame, [pts], True, ROI_COLOR, ROI_THICKNESS)
        cv2.putText(annotated_frame, "OBSTRUCTION DETECTION ZONE", 
                   (roi[0][0], roi[0][1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, ROI_COLOR, 2)
        
    obstacle_detections = detect_obstacles_in_roi(frame, camera_id)
    if len(obstacle_detections) > 0:
        has_obstacle = True
        all_detections.extend(obstacle_detections)
        
        # วาด bounding box สำหรับสิ่งกีดขวาง
        for obs in obstacle_detections:
            x1, y1, x2, y2 = obs['bbox']
            color = (0, 165, 255)  # สีส้ม (BGR)
            thickness = 3
            
            # วาด bbox
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            
            # วาด label
            label = f"⚠️ {obs['class']}: {obs['confidence']:.2f}"
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - text_h - 10), 
                         (x1 + text_w + 10, y1), color, -1)
            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # วาดจุดกึ่งกลาง
            cv2.circle(annotated_frame, ((x1+x2)//2, (y1+y2)//2), 5, color, -1)
    
    # Stage 1: Detect persons and forklifts
    person_results = model_manager.detect_persons(
        frame,
        conf_threshold=PERSON_CONFIDENCE_THRESHOLD
    )
    
    if person_results is None or len(person_results[0].boxes) == 0:
        return annotated_frame, all_detections, has_ng, has_obstacle
    
    # Process each detected person/forklift
    for person_idx, person_box in enumerate(person_results[0].boxes):
        person_conf = float(person_box.conf)
        person_bbox = person_box.xyxy[0].cpu().numpy()
        person_class_id = int(person_box.cls)
        person_class_name = model_manager.person_model.names[person_class_id]
        
        px1, py1, px2, py2 = map(int, person_bbox)
        
        # If forklift, just draw and skip PPE detection
        if person_class_name.lower() == 'forklift':
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (255, 0, 0), 2)
            label = f"Forklift: {person_conf:.2f}"
            
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (px1, py1 - text_h - 10), (px1 + text_w + 10, py1), (255, 0, 0), -1)
            cv2.putText(annotated_frame, label, (px1 + 5, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            all_detections.append({
                'type': 'forklift',
                'bbox': [px1, py1, px2, py2],
                'confidence': person_conf,
                'person_id': None
            })
            continue
        
        # Stage 2: Detect PPE within person bbox
        ppe_detections = detect_ppe_in_person(frame, person_bbox)
        
        # Stage 3: Classify each PPE detection
        for ppe in ppe_detections:
            bbox = ppe['bbox']
            x1, y1, x2, y2 = bbox
            class_name = ppe['class']
            det_conf = ppe['conf']
            
            # Classify PPE
            classified_name, class_conf, is_classified = classify_ppe_item(
                frame, bbox, class_name
            )
            
            # Skip if classification failed or confidence too low
            if not is_classified or class_conf < CLASSIFICATION_THRESHOLD:
                continue
            
            # Determine display name
            # display_name = classified_name.split('_', 1)[1] if '_' in classified_name else classified_name
            # display_name = display_name.replace('-', ' ').title()
            
            # Check if NG (non-safety)
            is_non_safety = 'non-safety' in classified_name.lower()
            
            if is_non_safety:
                has_ng = True
                color = (0, 0, 255)  # Red
                thickness = 4
            else:
                color = (0, 255, 0)  # Green
                thickness = 2
            
            # Store detection result
            all_detections.append({
                'type': 'ppe',
                'person_id': person_idx + 1,
                'bbox': bbox,
                'detected_class': class_name,
                'classified_as': classified_name,
                'detection_conf': round(det_conf, 2),
                'classification_conf': round(class_conf, 2),
                'is_ng': is_non_safety
            })
            
            # Draw PPE bbox
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label
            label = f"{classified_name}"
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), color, -1)
            cv2.putText(annotated_frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Draw center point
            cv2.circle(annotated_frame, ((x1+x2)//2, (y1+y2)//2), 5, color, -1)
    
    return annotated_frame, all_detections, has_ng, has_obstacle


def is_point_in_polygon(point, polygon):
    """
    Check if a point is inside a polygon using ray casting algorithm
    
    Args:
        point: Tuple (x, y)
        polygon: List of tuples [(x1, y1), (x2, y2), ...]
        
    Returns:
        bool: True if point is inside polygon
    """
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


def detect_obstacles_in_roi(frame, camera_id):
    """
    Detect obstacles within ROI zones
    
    Args:
        frame: Input frame
        camera_id: Camera ID for ROI zone selection
        
    Returns:
        list: List of obstacle detections
    """
    if not ENABLE_OBSTACLE_DETECTION:
        return []
    
    if camera_id not in ROI_ZONES:
        return []
    
    try:
        # Run obstacle detection on full frame
        obstacle_results = model_manager.detect_obstacles(
            frame,
            conf_threshold=OBSTACLE_CONFIDENCE_THRESHOLD
        )
        
        if obstacle_results is None or len(obstacle_results[0].boxes) == 0:
            return []
        
        # Filter detections that are inside ROI
        roi_polygon = ROI_ZONES[camera_id]
        obstacles_in_roi = []
        
        for box in obstacle_results[0].boxes:
            bbox = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = map(int, bbox)
            
            # Check if center point is in ROI
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            if is_point_in_polygon((center_x, center_y), roi_polygon):
                cls_id = int(box.cls)
                class_name = model_manager.obstacle_model.names[cls_id]
                conf = float(box.conf)
                
                obstacles_in_roi.append({
                    'type': 'obstacle',
                    'class': class_name,
                    'bbox': [x1, y1, x2, y2],
                    'confidence': conf,
                    'in_roi': True
                })
        
        return obstacles_in_roi
        
    except Exception as e:
        print(f"❌ Error in obstacle detection: {e}")
        return []