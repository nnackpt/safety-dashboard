export interface Camera {
  id: number;
  url: string;
  status: string;
  detections?: number;
}

export interface CameraInfo {
  id: number;
  url: string;
  status: string;
  resolution: string;
  detections: number;
}

export interface Detection {
  class: string;
  confidence: number;
  bbox: number[];
}

export interface DetectionData {
  camera_id: number;
  count: number;
  detections: Detection[];
}