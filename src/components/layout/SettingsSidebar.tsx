"use client";

import { X, Camera as CameraIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface SettingsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCamera: string;
  onCameraSelect: (camera: string) => void;
}

const CAMERA_OPTIONS = ["All Cameras", "Camera 1", "Camera 2"];

export default function SettingsSidebar({
  isOpen,
  onClose,
  selectedCamera,
  onCameraSelect,
}: SettingsSidebarProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/30 z-[9998]"
            onClick={onClose}
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-[9999] flex flex-col"
          >
            {/* Header */}
            <div className="bg-[#052c65] text-white p-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">Settings</h2>
              <button
                onClick={onClose}
                className="p-1 hover:bg-white hover:bg-opacity-20 rounded transition-colors"
              >
                <X size={24} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {/* Camera Selection Section */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                  <CameraIcon size={20} className="text-[#052c65]" />
                  Camera Selection
                </h3>
                
                <div className="space-y-2">
                  {CAMERA_OPTIONS.map((camera) => (
                    <button
                      key={camera}
                      onClick={() => onCameraSelect(camera)}
                      className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all cursor-pointer ${
                        selectedCamera === camera
                          ? "border-[#052c65] bg-blue-50 text-[#052c65] font-semibold"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700"
                      }`}
                    >
                      {camera}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4">
              <button
                onClick={onClose}
                className="w-full bg-[#052c65] text-white py-3 rounded-lg font-semibold hover:bg-[#073d5a] transition-colors cursor-pointer"
              >
                Apply Settings
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}