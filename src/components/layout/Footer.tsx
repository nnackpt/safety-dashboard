"use client";

import { useEffect, useState } from "react";

interface CameraStatus {
  id: number;
  url: string;
  status: string;
  detections?: number;
}

export default function Footer() {
  const apiUrl = "http://localhost:8083/api";
  const [cameras, setCameras] = useState<CameraStatus[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Initial fetch
    fetchCameraStatus();

    // Poll every 2 seconds
    const interval = setInterval(fetchCameraStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  const fetchCameraStatus = async () => {
    try {
      const response = await fetch(`${apiUrl}/cameras`);
      const data = await response.json();
      setCameras(data.cameras || []);
      setIsConnected(true);
    } catch (error) {
      console.error("Failed to fetch camera status:", error);
      setIsConnected(false);
    }
  };

  // Calculate overall status
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
    <footer className="w-full bg-[#2B2B2B] text-white py-3 text-xl">
      <div className="max-w-[1200px] mx-auto px-4">
        <div className="flex items-center justify-center gap-8">
          <div>
            <span className="opacity-80">Camera Status :</span>{" "}
            <span 
              className={`font-semibold ${
                cameraStatusText === "Online" ? "text-green-400" :
                cameraStatusText === "Partial" ? "text-yellow-400" :
                "text-red-400"
              }`}
            >
              {cameraStatusText}
            </span>
          </div>
          <div>
            <span className="opacity-80">Network :</span>{" "}
            <span 
              className={`font-semibold ${
                networkStatus === "Stable" ? "text-green-400" : "text-red-400"
              }`}
            >
              {networkStatus}
            </span>
          </div>
          <div>
            <span className="opacity-80">Status :</span>{" "}
            <span 
              className={`font-semibold ${
                overallStatus === "Ok" ? "text-green-400" :
                overallStatus === "Warning" ? "text-yellow-400" :
                "text-red-400"
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