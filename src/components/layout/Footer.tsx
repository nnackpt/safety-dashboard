"use client";

import { useEffect, useState } from "react";

interface CameraStatus {
  id: number;
  url: string;
  status: string;
  detections?: number;
}

export default function Footer() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://ath-ma-wd2503:8083/api"
  const [cameras, setCameras] = useState<CameraStatus[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    fetchCameraStatus();

    const interval = setInterval(fetchCameraStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  const fetchCameraStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/cameras`);
      const data = await response.json();
      setCameras(data.cameras || []);
      setIsConnected(true);
    } catch (error) {
      console.error("Failed to fetch camera status:", error);
      setIsConnected(false);
    }
  };

  const allCamerasActive = cameras.length > 0 && cameras.every(cam => cam.status === "active");
  const anyCameraActive = cameras.some(cam => cam.status === "active");
  
  const getCameraStatusText = () => {
    if (!isConnected) return "Disconnected";
    if (cameras.length === 0) return "No Cameras";
    if (allCamerasActive) return "Online";
    if (anyCameraActive) return "Partial";
    return "Offline";
  };

  const getNetworkStatus = () => {
    if (!isConnected) return "Disconnected";
    return "Stable";
  };

  const getOverallStatus = () => {
    if (!isConnected) return "Error";
    if (allCamerasActive) return "Ok";
    if (anyCameraActive) return "Warning";
    return "Error";
  };

  const cameraStatusText = getCameraStatusText();
  const networkStatus = getNetworkStatus();
  const overallStatus = getOverallStatus();

  return (
    <footer className="w-full bg-gray-50 text-gray-700 py-1.5 sm:py-2 text-xs sm:text-sm">
      <div className="max-w-[1200px] mx-auto px-3 sm:px-4">
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 md:gap-6">
          <div className="flex items-center gap-1">
            <span className="opacity-70">Camera Status :</span>{" "}
            <span 
              className={`font-semibold ${
                cameraStatusText === "Online" ? "text-green-600" :
                cameraStatusText === "Partial" ? "text-yellow-600" :
                "text-red-600"
              }`}
            >
              {cameraStatusText}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="opacity-70">Network :</span>{" "}
            <span 
              className={`font-semibold ${
                networkStatus === "Stable" ? "text-green-600" : "text-red-600"
              }`}
            >
              {networkStatus}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="opacity-70">Status :</span>{" "}
            <span 
              className={`font-semibold ${
                overallStatus === "Ok" ? "text-green-600" :
                overallStatus === "Warning" ? "text-yellow-600" :
                "text-red-600"
              }`}
            >
              {overallStatus}
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}