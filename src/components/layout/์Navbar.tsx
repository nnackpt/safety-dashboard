"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDown, Home, BarChart3, Settings, FileText, Users } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

interface MenuItem {
  label: string;
  icon: React.ReactNode;
  path?: string;
  submenu?: { label: string; path: string }[];
  action?: () => void;
}

interface NavbarProps {
  onSettingsClick?: () => void;
}

export default function Navbar({ onSettingsClick }: NavbarProps) {
  const router = useRouter();
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [pageTitle, setPageTitle] = useState("Slitting Process");

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };

    if (openDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [openDropdown]);

  const menuItems: MenuItem[] = [
    {
      label: "Home",
      icon: <Home size={18} />,
      submenu: [
        { label: "Slitting Process", path: "/" },
        { label: "Warehouse", path: "/warehouse" },
      ],
    },
    {
      label: "Dashboard",
      icon: <BarChart3 size={18} />,
      submenu: [
        { label: "Slitting Process", path: "/dashboard/slittingprocess" },
        { label: "Warehouse", path: "/dashboard/warehouse" },
      ],
    },
    {
      label: "Settings",
      icon: <Settings size={18} />,
      action: onSettingsClick,
    },
  ];

  const handleMenuClick = (item: MenuItem) => {
    if (item.action) {
      item.action();
      setOpenDropdown(null);
    } else if (item.path) {
      router.push(item.path);
      setOpenDropdown(null);
    } else if (item.submenu) {
      setOpenDropdown(openDropdown === item.label ? null : item.label);
    }
  };

  const handleSubmenuClick = (path: string, label: string) => {
    router.push(path);
    setOpenDropdown(null);
    setPageTitle(label)
  };

  return (
    <>
      <div className="bg-[#052c65] px-6 py-2 flex items-center justify-between">
        <div className="flex items-center">
          <img src="/logo.png" alt="Autoliv" className="h-6 sm:h-8" />
        </div>
        <div className="flex items-center gap-4">
          <h1 className="text-lg sm:text-xl font-bold text-white">{pageTitle}</h1>
        </div>
      </div>

      <nav className="bg-white shadow-md border-b border-gray-200" ref={dropdownRef}>
        <div className="max-w-[1800px] mx-auto px-2">
          <div className="flex items-center justify-start gap-1">
            {menuItems.map((item) => (
              <div key={item.label} className="relative">
                <button
                  onClick={() => handleMenuClick(item)}
                  className="flex items-center gap-2 px-3 py-2.5 text-gray-700 hover:bg-gray-100 hover:text-blue-700 transition-all duration-200 font-medium text-sm rounded-t-lg group cursor-pointer"
                >
                  <span className="text-gray-600 group-hover:text-blue-600 transition-colors">
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                  {item.submenu && (
                    <motion.div
                      animate={{ rotate: openDropdown === item.label ? 180 : 0 }}
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                      <ChevronDown size={16} />
                    </motion.div>
                  )}
                </button>

                {/* Dropdown Menu with AnimatePresence */}
                <AnimatePresence>
                  {item.submenu && openDropdown === item.label && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2, ease: "easeOut" }}
                      className="absolute top-full left-0 mt-0 w-56 bg-white border border-gray-200 rounded-b-lg shadow-lg z-50"
                    >
                      {item.submenu.map((subItem) => (
                        <button
                          key={subItem.label}
                          onClick={() => handleSubmenuClick(subItem.path, subItem.label)}
                          className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition-colors first:rounded-t-lg last:rounded-b-lg cursor-pointer"
                        >
                          {subItem.label}
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </nav>
    </>
  );
}