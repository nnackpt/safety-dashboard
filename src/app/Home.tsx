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

const API_URL = process.env.API_URL

export default function Home() {
  const [cameras, setCameras] = useState<Camera[]>([])
  const [error, setError] = useState<string | null>(null)
  const [cameraInfo, setCameraInfo] = useState<{ [key: number]: CameraInfo }>({})
  const [detections, setDetections] = useState<{ [key: number]: DetectionData }>({})
  const [selectedCameraId, setSelectedCameraId] = useState<number | null>(0)
  const [hasNG, setHasNG] = useState<boolean>(false)
  const [safetyViolations, setSafetyViolations] = useState<string[]>([])
  const [violationTypes, setViolationTypes] = useState<{
    glove: boolean;
    shoe: boolean;
    glasses: boolean;
    shirt: boolean;
  }>({
    glove: false,
    shoe: false,
    glasses: false,
    shirt: false
  })
  const shouldShowNG = hasNG || safetyViolations.length > 0

  const testScenario = (scenario: 'normal' | 'ng' | 'glove' | 'shoe' | 'glasses' | 'shirt' | 'violations' | 'all') => {
    const mockDetections: { [key: number]: DetectionData } = {};
    
    displayCameras.forEach(cameraId => {
      const mockData: Detection[] = [];
      
      // NG
      if (scenario === 'ng' || scenario === 'all') {
        mockData.push({
          class: "NG",
          confidence: 0.95,
          bbox: [100, 100, 200, 200]
        });
      }
      
      // Individual violations
      if (scenario === 'glove' || scenario === 'violations' || scenario === 'all') {
        mockData.push({
          class: "non-safety-glove",
          confidence: 0.88,
          bbox: [300, 150, 400, 250]
        });
      }
      
      if (scenario === 'shoe' || scenario === 'violations' || scenario === 'all') {
        mockData.push({
          class: "non-safety-shoe",
          confidence: 0.92,
          bbox: [500, 200, 600, 300]
        });
      }
      
      if (scenario === 'glasses' || scenario === 'violations' || scenario === 'all') {
        mockData.push({
          class: "non-safety-glasses",
          confidence: 0.85,
          bbox: [700, 100, 800, 200]
        });
      }
      
      if (scenario === 'shirt' || scenario === 'violations' || scenario === 'all') {
        mockData.push({
          class: "non-safety-shirt",
          confidence: 0.90,
          bbox: [900, 150, 1000, 250]
        });
      }
      
      mockDetections[cameraId] = {
        camera_id: cameraId,
        count: mockData.length,
        detections: mockData
      };
    });
    
    setDetections(mockDetections);
  };

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
    const checkDetections = () => {
      let foundNG = false;
      const violations = new Set<string>()
      const types = {
        glove: false,
        shoe: false,
        glasses: false,
        shirt: false
      };
      
      for (const cameraId of displayCameras) {
        const detection = detections[cameraId]
        if (detection?.detections) {
          detection.detections.forEach((d: Detection) => {
            const className = d.class.trim().toUpperCase()
            
            // Check for NG
            if (className === "NG") {
              foundNG = true;
            }
            
            // Check for safety violations
            if (className === "NON-SAFETY-GLOVE") {
              violations.add("Missing Safety Gloves")
              types.glove = true;
            } else if (className === "NON-SAFETY-SHOE") {
              violations.add("Missing Safety Shoes")
              types.shoe = true;
            } else if (className === "NON-SAFETY-GLASSES") {
              violations.add("Missing Safety Glasses")
              types.glasses = true;
            } else if (className === "NON-SAFETY-SHIRT") {
              violations.add("Missing Safety Vest")
              types.shirt = true;
            }
          })
        }
      }
      
      setHasNG(foundNG)
      setSafetyViolations(Array.from(violations))
      setViolationTypes(types)
    };
    
    checkDetections();
  }, [detections, displayCameras])

  // Get stream URL with single parameter
  const getStreamUrl = (cameraId: number) => {
    return `${API_URL}/camera/${cameraId}/stream/detected?single=${isSingleView}`;
  };

  return (
    <div className="flex-1 bg-[#09304F] px-2 sm:px-3 pt-2 sm:pt-3 pb-0 flex flex-col overflow-hidden">
      {/* Topbar Component */}
      <Topbar onCameraSelect={handleCameraSelect} />

      {/* Test Controls */}
      {/* <div className="bg-yellow-500/20 border-2 border-yellow-500 p-2 rounded">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-9 gap-2">
          <button onClick={() => testScenario('normal')} className="bg-green-600 hover:bg-green-700 px-2 py-1 rounded text-xs font-semibold">
            ✅ Normal
          </button>
          <button onClick={() => testScenario('ng')} className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs font-semibold">
            🚫 NG
          </button>
          <button onClick={() => testScenario('glove')} className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs font-semibold">
            🧤 Glove
          </button>
          <button onClick={() => testScenario('shoe')} className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs font-semibold">
            👟 Shoe
          </button>
          <button onClick={() => testScenario('glasses')} className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs font-semibold">
            🥽 Glasses
          </button>
          <button onClick={() => testScenario('shirt')} className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs font-semibold">
            👕 Vest
          </button>
          <button onClick={() => testScenario('violations')} className="bg-orange-600 hover:bg-orange-700 px-2 py-1 rounded text-xs font-semibold">
            ⚠️ All PPE
          </button>
          <button onClick={() => testScenario('all')} className="bg-purple-600 hover:bg-purple-700 px-2 py-1 rounded text-xs font-semibold">
            💥 All
          </button>
          <button onClick={() => setDetections({})} className="bg-gray-600 hover:bg-gray-700 px-2 py-1 rounded text-xs font-semibold">
            🔄 Clear
          </button>
        </div>
      </div> */}

      <div className="flex flex-col lg:grid lg:grid-cols-[1fr_300px] xl:grid-cols-[1fr_360px] gap-3 lg:gap-4 flex-1 min-h-0 mt-2 sm:mt-3">
        
        {/* ===== Left: Main Camera Display ===== */}
        <section className={`bg-[#09304F] border-4 sm:border-[6px] p-1 pt-0 pb-0 flex flex-col min-h-0 ${shouldShowNG ? 'border-red-600' : 'border-green-500'}`}>
          <div className={`flex gap-2 h-full items-center ${isSingleView ? 'justify-center' : ''}`}>
            {displayCameras.map((cameraId) => (
              <div 
                key={cameraId}
                className={`${isSingleView ? 'w-full h-full px-2 sm:px-4' : 'flex-1 h-full'} flex items-center justify-center`}
              >
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={getStreamUrl(cameraId)}
                    alt={`Camera ${cameraId + 1}`}
                    className="max-w-full max-h-full object-contain bg-black border-2 sm:border-[4px] border-black"
                  />
                  <div className="absolute top-1 sm:top-2 left-1 sm:left-2 bg-black bg-opacity-90 text-white px-2 sm:px-3 py-1 sm:py-2 text-[10px] sm:text-xs rounded z-10">
                    <div className="flex items-center gap-1 sm:gap-2">
                      <span className="font-bold text-xs sm:text-sm">Camera {cameraId + 1}</span>
                      <span className="text-xs sm:text-sm">{cameras[cameraId]?.status === "active" ? "🟢" : "🔴"}</span>
                    </div>
                    {cameraInfo[cameraId] && (
                      <div className="text-yellow-300 mt-0.5 sm:mt-1 text-[9px] sm:text-[10px]">
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
        <aside className="h-auto lg:h-full min-h-0 flex flex-col gap-3 sm:gap-4">
          {/* OK Panel */}
          <div className={`h-32 sm:h-40 lg:h-48 xl:h-[215px] border-4 sm:border-8 lg:border-[10px] border-[#005496] flex items-center justify-center ${shouldShowNG ? 'bg-[#CFCFCF]' : 'bg-green-500'}`}>
            <span className="text-5xl sm:text-6xl lg:text-7xl xl:text-[95px] leading-none font-extrabold text-black">OK</span>
          </div>

          {/* NG Panel */}
          <div className={`h-32 sm:h-40 lg:h-48 xl:h-[215px] border-4 sm:border-8 lg:border-[10px] border-[#005496] flex items-center justify-center ${shouldShowNG ? 'bg-red-600' : 'bg-[#CFCFCF]'}`}>
            <span className="text-5xl sm:text-6xl lg:text-7xl xl:text-[95px] leading-none font-extrabold text-black">NG</span>
          </div>

          {/* PPE REQUIREMENT */}
          <div className="bg-[#0B4A82] border-4 sm:border-[6px] border-[#005496] p-3 sm:p-4 flex-1 min-h-0 flex flex-col">
            <h3
              className="text-[#E5E5E5] font-bold text-lg sm:text-xl lg:text-2xl tracking-wide text-center"
              style={{ textShadow: "0 4px 0 rgba(0,0,0,.35)" }}
            >
              PPE REQUIREMENT
            </h3>

            <div className="mt-3 sm:mt-4 grid grid-cols-4 gap-2 sm:gap-4 lg:gap-6 justify-items-center">
            {[
              { src: "safety-footerwear.png", alt: "Safety Footwear", violationType: "shoe" },
              { src: "wear-goggle.png", alt: "Wear Goggle", violationType: "glasses" },
              { src: "wear-hand-protection.png", alt: "Wear Hand Protection", violationType: "glove" },
              { src: "wear-vest.png", alt: "Wear Vest", violationType: "shirt" },
            ].map(({ src, alt, violationType }) => {
              const hasViolation = violationTypes[violationType as keyof typeof violationTypes];
              return (
                <div
                  key={src}
                  className={`w-14 sm:w-16 lg:w-20 rounded-[4px] sm:rounded-[6px] bg-[#EDEDED] shadow-[0_4px_0_rgba(0,0,0,0.25)] sm:shadow-[0_6px_0_rgba(0,0,0,0.25)] p-1 sm:p-2 transition-all ${
                    hasViolation 
                      ? 'border-4 border-red-600 ring-2 ring-red-600 ring-offset-2' 
                      : 'border border-[#BFBFBF]'
                  }`}
                >
                  <div className="w-full aspect-square rounded-[2px] sm:rounded-[4px] overflow-hidden flex items-center justify-center">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={src}
                      alt={alt}
                      className="max-w-full max-h-full object-contain block"
                    />
                  </div>
                </div>
              );
            })}
          </div>

            {/* WARNING BANNER */}
            <div className="mt-4 sm:mt-6">
              <div className="relative rounded-[6px] sm:rounded-[10px] bg-[#F39C12] px-3 sm:px-5 py-2 sm:py-3">
                <div className="pointer-events-none absolute inset-0 rounded-[8px] sm:rounded-[12px] border-4 sm:border-[6px] border-black" />
                <div className="pointer-events-none absolute inset-[6px] sm:inset-[10px] rounded-[6px] sm:rounded-[8px] border sm:border-2 border-black" />
                <div className="relative">
                  <div className="flex items-center justify-center gap-1 bg-black rounded-[6px] sm:rounded-[8px] px-3 sm:px-5 py-1.5 sm:py-2">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="warning.png" alt="Warning" className="w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10 object-contain" />
                    <span className="text-[#FBBF24] text-xl sm:text-2xl lg:text-[30px] leading-none font-extrabold tracking-wide sm:tracking-widest">
                      WARNING
                    </span>
                  </div>
                  <div className="py-2 sm:py-3 text-center">
                    {shouldShowNG ? (
                      <div className="space-y-1">
                        {hasNG && (
                          <div className="text-[#8B1E1E] font-bold text-base sm:text-lg lg:text-xl">
                            🚫 NG DETECTED
                          </div>
                        )}
                        {safetyViolations.map((violation, index) => (
                          <div key={index} className="text-[#8B1E1E] font-bold text-sm sm:text-base lg:text-lg">
                            ⚠️ {violation}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[#8B1E1E] font-extrabold text-lg sm:text-xl lg:text-2xl tracking-wide">
                        ---
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded z-50 text-sm sm:text-base">
          {error}
        </div>
      )}
    </div>
  );
}