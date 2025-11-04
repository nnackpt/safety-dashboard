"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface CameraContextType {
  selectedCamera: string;
  setSelectedCamera: (camera: string) => void;
  selectedCameraId: number | null;
  setSelectedCameraId: (id: number | null) => void;
}

const CameraContext = createContext<CameraContextType | undefined>(undefined);

export function CameraProvider({ children }: { children: ReactNode }) {
  const [selectedCamera, setSelectedCamera] = useState("Camera 1");
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(0);

  return (
    <CameraContext.Provider 
      value={{ 
        selectedCamera, 
        setSelectedCamera,
        selectedCameraId,
        setSelectedCameraId 
      }}
    >
      {children}
    </CameraContext.Provider>
  );
}

export function useCameraContext() {
  const context = useContext(CameraContext);
  if (!context) {
    throw new Error("useCameraContext must be used within CameraProvider");
  }
  return context;
}