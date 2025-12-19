"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import StatusPanel from "@/components/StatusPanel";
import { Camera, CameraInfo, Detection, DetectionData } from "@/Types/Camera";
import { useCameraContext } from "@/contexts/CameraContext";
import { CheckCircle2, XCircle } from "lucide-react";
import { useConfig } from "@/hooks/useConfig";


export default function Warehouse() {
  const { config } = useConfig();
  const API_URL = config?.Warehouse.API_URL || "http://localhost:8084";

  const { selectedCameraId } = useCameraContext();

  const [cameras, setCameras] = useState<Camera[]>([])
  const [error, setError] = useState<string | null>(null)
  const [cameraInfo, setCameraInfo] = useState<{ [key: number]: CameraInfo }>({})
  const [detections, setDetections] = useState<{ [key: number]: DetectionData }>({})
  const [hasNG, setHasNG] = useState<boolean>(false)
  const [safetyViolations, setSafetyViolations] = useState<string[]>([])
  const [violationTypes, setViolationTypes] = useState<{
    helmet: boolean
    shoes: boolean
    vest: boolean
  }>({
    helmet: false,
    shoes: false,
    vest: false
  })

  // const [audioEnabled, setAudioEnabled] = useState(true)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlayingAlert, setIsPlayingAlert] = useState(false)
  const wakeLockRef = useRef<WakeLockSentinel | null>(null)
  
  const [streamReloadKey, setStreamReloadKey] = useState<{ [key: number]: number }>({})
  const streamErrorCount = useRef<{ [key: number]: number }>({})
  const streamLoadSuccess = useRef<{ [key: number]: boolean }>({})
  // const [testMode, setTestMode] = useState(false)
  const shouldShowNG = hasNG || safetyViolations.length > 0
  const [audioInitialized, setAudioInitialized] = useState(false)

  // Wake Lock: Keep screen awake
  useEffect(() => {
    const requestWakeLock = async () => {
      try {
        if ('wakeLock' in navigator) {
          wakeLockRef.current = await navigator.wakeLock.request('screen')
          console.log('Wake Lock activated - screen will stay on')
        }
      } catch (err) {
        console.error('Wake Lock error:', err)
      }
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && wakeLockRef.current === null) {
        requestWakeLock()
      }
    }

    requestWakeLock()
    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      if (wakeLockRef.current) {
        wakeLockRef.current.release()
        wakeLockRef.current = null
        console.log('Wake Lock released')
      }
    }
  }, [])

  // Fetch cameras list
  useEffect(() => {
    fetch(`${API_URL}/cameras`)
      .then((res) => res.json())
      .then((data) => {
        console.log("📹 Cameras data:", data.cameras)
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
    console.log("🔄 Setting up detection polling with API_URL:", API_URL);
    
    const interval = setInterval(() => {
      cameras.forEach((cam) => {
        const detectionUrl = `${API_URL}/camera/${cam.id}/detections`;
        console.log(`📡 Fetching from: ${detectionUrl}`);
        
        fetch(detectionUrl)
          .then((res) => {
            console.log(`✅ Response status for camera ${cam.id}:`, res.status);
            return res.json();
          })
          .then((data: DetectionData) => {
            console.log(`📦 [Camera ${cam.id}] Raw API Response:`, data);
            
            setDetections((prev) => {
              const updated = { ...prev, [cam.id]: data };
              console.log(`💾 Updated detections state:`, updated);
              return updated;
            });
          })
          .catch((err) => {
            console.error(`❌ Error fetching camera ${cam.id}:`, err);
          });
      });
    }, 500);

    return () => {
      console.log("🛑 Clearing detection polling interval");
      clearInterval(interval);
    };
  }, [cameras, API_URL])

  useEffect(() => {
    const audio = new Audio('/emergency-alarmsiren-type.mp3');
    audio.volume = 0.8;
    audio.loop = true;

    audio.addEventListener("canplaythrough", () => {
      console.log("✅ Audio file loaded")
    })

    audio.addEventListener("error", (e) => {
      console.error("❌ Audio file error:", e)
    })

    audioRef.current = audio;
    audio.load();
    
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.src = ""
        audioRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    const initAudio = () => {
      if (!audioInitialized && audioRef.current) {
        audioRef.current.play().then(() => {
          audioRef.current!.pause()
          audioRef.current!.currentTime = 0
          setAudioInitialized(true)
          console.log("✅ Audio initialized")
        }).catch(() => {
          console.log("⚠️ Audio requires user interaction")
        })
      }
    }

    // Try initialize on first click/touch
    const events = ['click', 'touchstart', 'keydown', 'mousemove'];
    events.forEach(event => {
      document.addEventListener(event, initAudio, { once: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, initAudio)
      })
    }
  }, [audioInitialized])

  const displayCameras = selectedCameraId === null ? [0, 1] : [selectedCameraId];
  const isSingleView = displayCameras.length === 1;

  useEffect(() => {
    console.log("Current selectedCameraId:", selectedCameraId);
    console.log("Display cameras:", displayCameras);
  }, [selectedCameraId, displayCameras]);

  // Check for NG detections
  useEffect(() => {
    const checkDetections = () => {
      console.log("🔍 CHECK DETECTIONS");
      
      let foundNG = false;
      const violations = new Set<string>();
      const types = {
        helmet: false,
        shoes: false,
        vest: false
      };
      
      for (const cameraId of displayCameras) {
        const detection = detections[cameraId];
        console.log(`[Camera ${cameraId}]:`, detection);
        
        if (detection?.detections) {
          console.log(` Detections: ${detection.detections.length}`);
          
          detection.detections.forEach((d: Detection, idx: number) => {
            console.log(`\n  [${idx}]:`, {
              class: d.class,
              classified_as: d.classified_as,
              is_ng: d.is_ng
            });
            
            // ⭐ เช็ค is_ng ก่อน
            if (d.is_ng === true) {
              foundNG = true;
              console.log("    ✅ is_ng = true");
            }
            
            const classifiedName = (d.classified_as || d.class || "").trim().toLowerCase();
            
            if (classifiedName === "non-safety-helmet") {
              foundNG = true;
              violations.add("Missing Safety Helmet");
              types.helmet = true;
            } else if (classifiedName === "non-safety-shoes") {
              foundNG = true;
              violations.add("Missing Safety Shoes");
              types.shoes = true;
            } else if (classifiedName === "non-safety-vest") {
              foundNG = true;
              violations.add("Missing Safety Vest");
              types.vest = true;
            }
          });
        }
      }
      
      const newViolations = Array.from(violations);
      
      console.log("\n📊 Results:", {
        foundNG,
        violations: newViolations
      });
      
      setHasNG(foundNG);
      setSafetyViolations(newViolations);
      setViolationTypes(types);
    };
    
    checkDetections();
  }, [detections, displayCameras]);

  useEffect(() => {
    console.log("Audio Effect:", {
      shouldShowNG,
      isPlayingAlert,
      audioInitialized,
      audioRefExists: !!audioRef.current
    })
    let timeoutId: NodeJS.Timeout;
    
    if (shouldShowNG && !isPlayingAlert && audioInitialized) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0
        audioRef.current.loop = true
        audioRef.current.play()
          .then(() => {
            setIsPlayingAlert(true)
            console.log("🔊 Alert playing")
          })
          .catch(err => {
            console.error("Play failed:", err)
            setTimeout(() => {
              audioRef.current?.play()
                .then(() => setIsPlayingAlert(true))
                .catch(e => console.error("Retry failed:", e))
            }, 500);
          }
        )
      }
    } else if (!shouldShowNG && isPlayingAlert) {
      timeoutId = setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.pause()
          audioRef.current.currentTime = 0
          setIsPlayingAlert(false)
          console.log("🔇 Alert stopped")
        }
      }, 2000)
    } else if (isPlayingAlert) {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
        setIsPlayingAlert(false)
      }
    }
    
    return () => {
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [shouldShowNG, isPlayingAlert, audioInitialized])

  const getStreamUrl = (cameraId: number) => {
    const key = streamReloadKey[cameraId] || 0;
    return `${API_URL}/camera/${cameraId}/stream/detected?single=${isSingleView}&v=${key}`;
  };

  // ⭐ Handle stream errors
   const handleStreamError = useCallback((cameraId: number) => {
    streamErrorCount.current[cameraId] = (streamErrorCount.current[cameraId] || 0) + 1;
    
    console.log(`⚠️ Camera ${cameraId + 1} stream error (count: ${streamErrorCount.current[cameraId]})`);
    
    if (streamErrorCount.current[cameraId] >= 5) {
      console.log(`🔄 Camera ${cameraId + 1} reloading stream...`);
      
      setStreamReloadKey(prev => ({
        ...prev,
        [cameraId]: (prev[cameraId] || 0) + 1
      }));
      
      // Reset error count
      streamErrorCount.current[cameraId] = 0;
      streamLoadSuccess.current[cameraId] = false;
    }
  }, []);

  // ⭐ Reset stream errors when stream loads successfully
  const handleStreamLoad = useCallback((cameraId: number) => {
    streamErrorCount.current[cameraId] = 0;
    streamLoadSuccess.current[cameraId] = true;
    console.log(`✅ Camera ${cameraId + 1} stream loaded successfully`);
  }, []);

  return (
    // <div className="flex-1 bg-[#09304F] px-2 pt-2 pb-0 flex flex-col overflow-hidden">
    <div className="flex-1 bg-[#09304F] flex flex-col overflow-hidden">
      {/* <Topbar onCameraSelect={handleCameraSelect} /> */}
      {/* <Navbar /> */}

      <div className="flex flex-col lg:grid lg:grid-cols-[1fr_auto] gap-2 lg:gap-3 flex-1 min-h-0 mt-2 lg:pr-1.5 xl:pr-3">
        {/* <button
          onClick={() => setTestMode(!testMode)}
          className={`fixed bottom-24 right-4 z-50 px-4 py-2 rounded-lg font-bold shadow-lg transition-all
            ${testMode 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-gray-700 hover:bg-gray-800 text-white'
            }`}
        >
          {testMode ? '🔴 Test ON' : '⚪ Test OFF'}
        </button> */}
        
        <section className={`bg-[#09304F] border-3 sm:border-4 p-1 pt-0 pb-0 flex flex-col min-h-0 ${
          shouldShowNG ? 'border-red-600' : 'border-green-500'
        }`}>
          <div className={`flex gap-2 h-full items-center ${isSingleView ? 'justify-center' : ''}`}>
            {displayCameras.map((cameraId) => (
              <div 
                key={cameraId}
                className={`${
                  isSingleView ? 'w-full h-full px-2 sm:px-4' : 'flex-1 h-full'
                } flex items-center justify-center`}
              >
                <div className="relative w-full h-full flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    key={streamReloadKey[cameraId] || 0}
                    src={getStreamUrl(cameraId)}
                    alt={`Camera ${cameraId + 1}`}
                    className="max-w-full max-h-full object-contain bg-black border-2 sm:border-[4px] border-black"
                    onError={() => handleStreamError(cameraId)}
                    onLoad={() => handleStreamLoad(cameraId)}
                  />
                  
                  <div className="absolute top-1 sm:top-2 left-1 sm:left-2 bg-black bg-opacity-90 text-white px-2 sm:px-3 py-1 sm:py-2 text-[10px] sm:text-xs rounded z-10">
                    <div className="flex items-center gap-1 sm:gap-2">
                      <span className="font-bold text-xs sm:text-sm">Camera {cameraId + 1}</span>
                      {cameras[cameraId]?.status === "active" ? (
                        <CheckCircle2
                          size={16} 
                          className="text-green-500 fill-green-500/20" 
                          strokeWidth={2.5}
                        />
                      ) : (
                        <XCircle
                          size={16} 
                          className="text-red-500 fill-red-500/20" 
                          strokeWidth={2.5}
                        />
                      )}
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

        <StatusPanel
          mode="warehouse"
          hasNG={hasNG}
          safetyViolations={safetyViolations}
          violationTypes={violationTypes}
        />
      </div>

      {error && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded z-50 text-sm sm:text-base">
          {error}
        </div>
      )}
    </div>
  );
}