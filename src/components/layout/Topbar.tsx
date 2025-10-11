"use client";

import { useEffect, useState } from "react";
import { BarChart3, Camera as CameraIcon, ChevronDown, Clock } from "lucide-react";
import { useRouter } from "next/navigation";

function formatDateTime(d: Date) {
  const pad = (n: number) => String(n).padStart(2, "0");
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const yyyy = d.getFullYear();
  let h = d.getHours();
  const ampm = h >= 12 ? "PM" : "AM";
  h = h % 12 || 12;
  const hh = pad(h);
  const mi = pad(d.getMinutes());
  const ss = pad(d.getSeconds());
  return `${mm}/${dd}/${yyyy} • ${hh}:${mi}:${ss} ${ampm}`;
}

const CAMERA_OPTIONS = ["All Cameras", "Camera 1", "Camera 2"];

export interface TopbarProps {
  onCameraSelect?: (camera: string) => void;
}

export default function Topbar({ onCameraSelect }: TopbarProps) {
  const router = useRouter();
  const [selectedCamera, setSelectedCamera] = useState(CAMERA_OPTIONS[1])
  const [open, setOpen] = useState(false)
  const [now, setNow] = useState<Date | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    if (onCameraSelect) {
      onCameraSelect(CAMERA_OPTIONS[1])
    }
  }, []);

  useEffect(() => {
    setMounted(true);
    setNow(new Date());
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const handleCameraChange = (camera: string) => {
    setSelectedCamera(camera);
    setOpen(false);
    if (onCameraSelect) {
      onCameraSelect(camera);
    }
  };

  return (
    <div className="w-full bg-[#0B4A82] text-white flex flex-col sm:flex-row items-center justify-between px-3 sm:px-6 py-2 sm:py-3 gap-3 sm:gap-0">
      {/* Logo */}
      <div className="flex items-center gap-4 sm:gap-8 md:gap-12 lg:gap-16 xl:gap-[0.9in] w-full sm:w-auto justify-between sm:justify-start">
        <img
          src="logo.png"   
          alt="Autoliv"
          className="h-8 sm:h-10 w-auto object-contain"
        />

        <div className="flex items-center gap-3">
          {/* Camera Selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setOpen(v => !v)}
              className="flex items-center gap-2 sm:gap-3 bg-[#2F2F2F] text-white border border-[#CFCFCF] rounded-[2px] px-3 sm:px-4 py-1.5 sm:py-2 leading-none text-sm sm:text-base"
            >
              <CameraIcon size={16} strokeWidth={3} className="text-white sm:w-5 sm:h-5" aria-hidden />
              <span className="text-base sm:text-lg lg:text-[20px]">{selectedCamera}</span>
              <ChevronDown size={16} className="opacity-90 sm:w-[18px] sm:h-[18px]" />
            </button>

            {open && (
              <ul className="absolute left-0 mt-1 w-full bg-[#2F2F2F] text-white border border-[#CFCFCF] rounded-[2px] overflow-hidden z-50">
                {CAMERA_OPTIONS.map(opt => (
                  <li key={opt}>
                    <button
                      className={`w-full text-left px-3 sm:px-4 py-1.5 sm:py-2 text-sm sm:text-base hover:bg-[#3A3A3A] ${
                        selectedCamera === opt ? "bg-[#3A3A3A]" : ""
                      }`}
                      onClick={() => handleCameraChange(opt)}
                    >
                      {opt}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* เพิ่มปุ่ม Dashboard */}
          <button
            type="button"
            onClick={() => router.push('/dashboard')}
            className="flex items-center gap-2 bg-[#F39C12] hover:bg-[#E67E22] text-white rounded-[2px] px-3 sm:px-4 py-1.5 sm:py-2 leading-none text-sm sm:text-base transition-colors cursor-pointer"
          >
            <BarChart3 size={16} strokeWidth={2.5} className="sm:w-5 sm:h-5" />
            <span className="text-base sm:text-lg lg:text-[20px] font-semibold">Dashboard</span>
          </button>
        </div>
      </div>

      {/* Date and Time */}
      <div className="flex items-center gap-2 text-sm sm:text-base lg:text-lg xl:text-[20px]">
        <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-white flex items-center justify-center">
          <span className="text-[#0B4A82] text-base sm:text-lg lg:text-[20px]">
            <Clock
              className="w-4 h-4 sm:w-5 sm:h-5 lg:w-[20px] lg:h-[20px] text-[#0B4A82]"
              strokeWidth={2.25}
            />
          </span>
        </span>
        <span suppressHydrationWarning className="whitespace-nowrap">
          {mounted && now ? formatDateTime(now) : ""}
        </span>
      </div>
    </div>
  );
}