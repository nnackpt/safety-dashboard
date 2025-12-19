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
  classified_as: string | null;
  detection_conf: number;
  classification_conf: number | null;
  bbox: number[];
  is_ng?: boolean
}

export interface DetectionData {
  camera_id: number;
  count: number;
  detections: Detection[];
}