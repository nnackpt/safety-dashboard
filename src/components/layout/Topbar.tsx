"use client";

import { useEffect, useState } from "react";
import { Camera as CameraIcon, ChevronDown } from "lucide-react";

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
  const [selectedCamera, setSelectedCamera] = useState(CAMERA_OPTIONS[1]); // เปลี่ยนจาก [0] เป็น [1] = "Camera 1"
  const [open, setOpen] = useState(false);
  const [now, setNow] = useState<Date | null>(null);
  const [mounted, setMounted] = useState(false);

  // เรียก onCameraSelect ตอน mount เพื่อตั้งค่า default
  useEffect(() => {
    if (onCameraSelect) {
      onCameraSelect(CAMERA_OPTIONS[1]); // ส่งค่า "Camera 1" ไปให้ parent
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
    <div className="w-full bg-[#0B4A82] text-white flex items-center justify-between px-6 py-3">
      {/* ซ้าย: โลโก้ + ปุ่มเลือกกล้อง */}
      <div className="flex items-center gap-[0.9in]">
        <img
          src="logo.png"   
          alt="Autoliv"
          className="h-10 w-[130px] object-contain"
        />

        {/* ปุ่มเลือกกล้อง */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setOpen(v => !v)}
            className="flex items-center gap-3 bg-[#2F2F2F] text-white border border-[#CFCFCF] rounded-[2px] px-4 py-2 leading-none"
          >
            <CameraIcon size={20} strokeWidth={3} className="text-white" aria-hidden />
            <span className="text-[20px]">{selectedCamera}</span>
            <ChevronDown size={18} className="opacity-90" />
          </button>

          {open && (
            <ul className="absolute left-0 mt-1 w-full bg-[#2F2F2F] text-white border border-[#CFCFCF] rounded-[2px] overflow-hidden z-50">
              {CAMERA_OPTIONS.map(opt => (
                <li key={opt}>
                  <button
                    className={`w-full text-left px-4 py-2 hover:bg-[#3A3A3A] ${
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
      </div>

      {/* ขวา: เวลาแบบเรียลไทม์ */}
      <div className="flex items-center gap-2 text-[20px]">
        <span className="w-6 h-6 rounded-full bg-white flex items-center justify-center">
          <span className="text-[#0B4A82] text-[20px]">🕒</span>
        </span>
        <span suppressHydrationWarning>
          {mounted && now ? formatDateTime(now) : ""}
        </span>
      </div>
    </div>
  );
}