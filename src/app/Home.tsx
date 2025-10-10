"use client";

import { useEffect, useState, useCallback } from "react";
import Topbar from "@/components/layout/Topbar";

interface Camera {
  id: number;
  url: string;
  status: string;
  detections?: number;
}

interface CameraInfo {
  id: number;
  url: string;
  status: string;
  resolution: string;
  detections: number;
}

interface Detection {
  class: string;
  confidence: number;
  bbox: number[];
}

interface DetectionData {
  camera_id: number;
  count: number;
  detections: Detection[];
}

const API_URL = "http://localhost:8083/api"

export default function Home() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cameraInfo, setCameraInfo] = useState<{ [key: number]: CameraInfo }>({});
  const [detections, setDetections] = useState<{ [key: number]: DetectionData }>({});
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(0);
  const [hasNG, setHasNG] = useState<boolean>(false);

  // Fetch cameras list
  useEffect(() => {
    fetch(`${API_URL}/cameras`)
      .then((res) => res.json())
      .then((data) => {
        setCameras(data.cameras || []);
        (data.cameras || []).forEach((cam: Camera) => {
          fetch(`${API_URL}/camera/${cam.id}`)
            .then((res) => res.json())
            .then((info: CameraInfo) => {
              setCameraInfo((prev) => ({ ...prev, [cam.id]: info }));
            })
            .catch((err) => console.error(`Error fetching camera ${cam.id} info:`, err));
        });
      })
      .catch((err) => {
        setError("Cannot connect to camera API");
        console.error(err);
      });
  }, []);

  // Poll detection results every 500ms
  useEffect(() => {
    const interval = setInterval(() => {
      cameras.forEach((cam) => {
        fetch(`${API_URL}/camera/${cam.id}/detections`)
          .then((res) => res.json())
          .then((data: DetectionData) => {
            setDetections((prev) => ({ ...prev, [cam.id]: data }));
          })
          .catch((err) => console.error(`Error fetching detections for camera ${cam.id}:`, err));
      });
    }, 500);

    return () => clearInterval(interval);
  }, [cameras]);

  // Handle camera selection from Topbar
  const handleCameraSelect = useCallback((cameraName: string) => {
    console.log("Camera selected:", cameraName);
    
    if (cameraName === "All Cameras") {
      setSelectedCameraId(null); 
      return;
    }
    
    // Camera 1 = id 0, Camera 2 = id 1
    const match = cameraName.match(/Camera (\d+)/);
    if (match) {
      const cameraNumber = parseInt(match[1]);
      const cameraId = cameraNumber - 1;
      console.log("Setting camera ID to:", cameraId);
      setSelectedCameraId(cameraId);
    }
  }, []);

  const displayCameras = selectedCameraId === null ? [0, 1] : [selectedCameraId];
  const isSingleView = displayCameras.length === 1;

  // Check for NG detections
  useEffect(() => {
    const checkNG = () => {
      for (const cameraId of displayCameras) {
        const detection = detections[cameraId];
        if (detection?.detections) {
          const hasNGDetection = detection.detections.some(
            (d: Detection) => d.class.trim().toUpperCase() === "NG"
          );
          if (hasNGDetection) {
            setHasNG(true);
            return;
          }
        }
      }
      setHasNG(false);
    };
    
    checkNG();
  }, [detections, displayCameras]);

  // Get stream URL with single parameter
  const getStreamUrl = (cameraId: number) => {
    return `${API_URL}/camera/${cameraId}/stream/detected?single=${isSingleView}`;
  };

  return (
    <div className="flex-1 bg-[#09304F] px-3 pt-3 pb-0 flex flex-col overflow-hidden">
      {/* Topbar Component */}
      <Topbar onCameraSelect={handleCameraSelect} />

      <div className="grid grid-cols-[1fr_360px] gap-4 flex-1 min-h-0 mt-3">
        {/* ===== Left: Main Camera Display ===== */}
        <section className={`bg-[#09304F] border-[6px] p-1 pt-0 pb-0 flex flex-col min-h-0 ${hasNG ? 'border-red-600' : 'border-green-500'}`}>
          <div className={`flex gap-2 h-full items-center ${isSingleView ? 'justify-center' : ''}`}>
            {displayCameras.map((cameraId) => (
              <div 
                key={cameraId}
                className={`${isSingleView ? 'w-full h-full px-4' : 'flex-1 h-full'} flex items-center justify-center`}
              >
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getStreamUrl(cameraId)}
                    alt={`Camera ${cameraId + 1}`}
                    className="max-w-full max-h-full object-contain bg-black border-[4px] border-black"
                  />
                  <div className="absolute top-2 left-2 bg-black bg-opacity-90 text-white px-3 py-2 text-xs rounded z-10">
                    <div className="flex items-center gap-2">
                      <span className="font-bold">Camera {cameraId + 1}</span>
                      <span>{cameras[cameraId]?.status === "active" ? "🟢" : "🔴"}</span>
                    </div>
                    {cameraInfo[cameraId] && (
                      <div className="text-yellow-300 mt-1 text-[10px]">
                        {cameraInfo[cameraId].resolution}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ===== Right: Status Panels ===== */}
        <aside className="h-full min-h-0 flex flex-col gap-4">
          {/* OK Panel */}
          <div className={`h-[215px] border-[10px] border-[#005496] flex items-center justify-center ${hasNG ? 'bg-[#CFCFCF]' : 'bg-green-500'}`}>
            <span className="text-[95px] leading-none font-extrabold text-black">OK</span>
          </div>

          {/* NG Panel */}
          <div className={`h-[215px] border-[10px] border-[#005496] flex items-center justify-center ${hasNG ? 'bg-red-600' : 'bg-[#CFCFCF]'}`}>
            <span className="text-[95px] leading-none font-extrabold text-black">NG</span>
          </div>

          {/* PPE REQUIREMENT */}
          <div className="bg-[#0B4A82] border-[6px] border-[#005496] p-4 flex-1 min-h-0 flex flex-col">
            <h3
              className="text-[#E5E5E5] font-bold text-[24px] tracking-wide text-center"
              style={{ textShadow: "0 6px 0 rgba(0,0,0,.35)" }}
            >
              PPE REQUIREMENT
            </h3>

            <div className="mt-4 grid grid-cols-4 gap-6 justify-items-center">
              {[
                { src: "safety-footerwear.png", alt: "Safety Footwear" },
                { src: "wear-goggle.png", alt: "Wear Goggle" },
                { src: "wear-hand-protection.png", alt: "Wear Hand Protection" },
                { src: "wear-vest.png", alt: "Wear Vest" },
              ].map(({ src, alt }) => (
                <div
                  key={src}
                  className="w-[80px] rounded-[6px] bg-[#EDEDED] border border-[#BFBFBF] shadow-[0_6px_0_rgba(0,0,0,0.25)] p-2"
                >
                  <div className="w-full h-[96px] rounded-[4px] overflow-hidden flex items-center justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={src}
                      alt={alt}
                      className="max-w-full max-h-full object-contain block"
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* WARNING BANNER */}
            <div className="mt-6">
              <div className="relative rounded-[10px] bg-[#F39C12] px-5 py-3">
                <div className="pointer-events-none absolute inset-0 rounded-[12px] border-[6px] border-black" />
                <div className="pointer-events-none absolute inset-[10px] rounded-[8px] border-2 border-black" />
                <div className="relative">
                  <div className="flex items-center gap-1 bg-black rounded-[8px] px-5 py-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="warning.png" alt="Warning" className="w-10 h-10 object-contain" />
                    <span className="text-[#FBBF24] text-[30px] leading-none font-extrabold tracking-widest">
                      WARNING
                    </span>
                  </div>
                  <div className="py-3 text-center">
                    <span className="text-[#8B1E1E] font-extrabold text-2xl tracking-wide">
                      ---
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded z-50">
          {error}
        </div>
      )}
    </div>
  );
}