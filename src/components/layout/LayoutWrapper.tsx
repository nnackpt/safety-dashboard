"use client";

import { useState, useCallback } from "react";
import Navbar from "@/components/layout/์Navbar";
import SettingsSidebar from "@/components/layout/SettingsSidebar";
import { useCameraContext } from "@/contexts/CameraContext";

interface LayoutWrapperProps {
  children: React.ReactNode;
}

export default function LayoutWrapper({ children }: LayoutWrapperProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { selectedCamera, setSelectedCamera, setSelectedCameraId } = useCameraContext();

  const handleCameraSelect = useCallback((cameraName: string) => {
    console.log("Camera selected:", cameraName);
    setSelectedCamera(cameraName);
    
    if (cameraName === "All Cameras") {
      setSelectedCameraId(null);
      return;
    }
    
    const match = cameraName.match(/Camera (\d+)/);
    if (match) {
      const cameraNumber = parseInt(match[1]);
      const cameraId = cameraNumber - 1;
      console.log("Setting camera ID to:", cameraId);
      setSelectedCameraId(cameraId);
    }
  }, [setSelectedCamera, setSelectedCameraId]);

  return (
    <>
      <Navbar onSettingsClick={() => setIsSettingsOpen(true)} />
      
      <SettingsSidebar
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        selectedCamera={selectedCamera}
        onCameraSelect={handleCameraSelect}
      />
      
      {children}
    </>
  );
}