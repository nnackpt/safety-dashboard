"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieLabelRenderProps,
} from "recharts";

interface MonthlyDataItem {
  month: string;
  gloves: number;
  glasses: number;
  shirt: number;
  empty: number;
}

export default function Dashboard() {
  const router = useRouter();
  
  const [stats, setStats] = useState({
    todayDetections: 0,
    yesterdayDetections: 0,
    totalNG: 0,
  });
  
  const [ppeStatusData, setPpeStatusData] = useState([
    { name: "OK", value: 0, color: "#47E0C4" },
    { name: "NG", value: 0, color: "#E66F71" },
  ]);
  
  const [monthlyData, setMonthlyData] = useState([
    { month: "Jan", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Feb", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Mar", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Apr", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "May", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Jun", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Jul", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Aug", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Sep", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Oct", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Nov", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
    { month: "Dec", gloves: 0, glasses: 0, shirt: 0, empty: 1 },
  ]);

  const ppeColors = {
    gloves: "#E3BCF9",
    glasses: "#EBA294",
    shirt: "#FDD573",
    empty: "#E5E7EB"
  };
  
  const [ruleViolations, setRuleViolations] = useState([
    { rule: "Safety Gloves", count: 0 },
    { rule: "Safety Glasses", count: 0 },
    { rule: "Safety Shirt", count: 0 },
    { rule: "Safety Shoes", count: 0 },
  ]);

  const [visiblePPE, setVisiblePPE] = useState({
    gloves: true,
    glasses: true,
    shirt: true,
  });

  const togglePPEVisibility = (key: 'gloves' | 'glasses' | 'shirt') => {
    setVisiblePPE(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };
  
  const [loading, setLoading] = useState(true);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  
  const ruleColors = ["#E3BCF9", "#EBA294", "#FDD573", "#BCE3EA"];
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://ath-ma-wd2503:8083/api";

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        
        // Fetch main stats
        const statsResponse = await fetch(`${API_URL}/dashboard/stats`);
        const statsData = await statsResponse.json();
        if (statsData.success) {
          setStats({
            todayDetections: statsData.todayDetections,
            yesterdayDetections: statsData.yesterdayDetections,
            totalNG: statsData.totalNG,
          });
        }

        // Fetch PPE status
        const ppeResponse = await fetch(`${API_URL}/dashboard/ppe-status`);
        const ppeData = await ppeResponse.json();
        if (ppeData.success) {
          setPpeStatusData(ppeData.data);
        }

        // Fetch rule violations
        const ruleResponse = await fetch(`${API_URL}/dashboard/rule-violations`);
        const ruleData = await ruleResponse.json();
        if (ruleData.success) {
          setRuleViolations(ruleData.data);
        }

        // Fetch monthly summary
        const monthlyResponse = await fetch(`${API_URL}/dashboard/monthly-summary`);
        const monthlyDataResponse = await monthlyResponse.json();
        if (monthlyDataResponse.success) {
          const processedData = monthlyDataResponse.data.map((item: MonthlyDataItem) => {
            const hasData = item.gloves > 0 || item.glasses > 0 || item.shirt > 0;
            return {
              ...item,
              empty: hasData ? 0 : 150
            };
          });
          setMonthlyData(processedData);
        }

      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
        setIsInitialLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [API_URL]);

  // ✅ Loading State
  if (isInitialLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#09304F] text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          <p className="text-xl">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-white text-white overflow-hidden">
      {/* Header */}
      <div className="bg-[#0B4A82] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center">
          <img src="/logo.png" alt="Autoliv" className="h-8 sm:h-10" />
        </div>
        <div className="flex items-center gap-4">
          <h1 className="text-xl sm:text-2xl font-bold">Safety Dashboard</h1>
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 bg-[#2F2F2F] hover:bg-[#3A3A3A] px-3 py-2 rounded text-sm transition-colors cursor-pointer"
          >
            <ArrowLeft size={18} />
            <span>Back to Monitor</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[1800px] mx-auto p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4">
          {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2 sm:gap-3 lg:gap-4">
              <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3 text-gray-700">Today&apos;s Detection</p>
                  <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg p-4 sm:p-5 shadow-md">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold text-white">NG</span>
                      <span className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">{stats.todayDetections}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3 text-gray-700">Yesterday Detection</p>
                  <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg p-4 sm:p-5 shadow-md">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold text-white">NG</span>
                      <span className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">{stats.yesterdayDetections}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3 text-gray-700">Total NG</p>
                  <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg p-4 sm:p-5 shadow-md">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold text-white">NG</span>
                      <span className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">{stats.totalNG}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-1 sm:gap-2">
            {/* Today's PPE NG Case */}
            <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg [&_*]:outline-none [&_*:focus]:outline-none">
              <div className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 shadow-md">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3 text-gray-800">
                  Today&apos;s PPE NG Case
                </h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                  <PieChart>
                    <Pie
                      data={ppeStatusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={(props: PieLabelRenderProps) => {
                        const { name, percent } = props as { name?: string; percent?: number };
                        const n = typeof name === "string" ? name : String(name ?? "");
                        const p = typeof percent === "number" ? (percent * 100).toFixed(0) : "0";
                        return `${n}: ${p}%`;
                      }}
                      outerRadius="90%"
                      fill="#8884d8"
                      dataKey="value"
                      style={{ fontSize: "16px", fontWeight: '700' }}
                      isAnimationActive={false}
                    >
                      {ppeStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: "#FFFFFF",
                        border: "1px solid #E5E7EB",
                        fontSize: "12px",
                        color: "#000000"
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Frequency of NG Events */}
            <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg [&_*]:outline-none [&_*:focus]:outline-none">
              <div className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 shadow-md">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3 text-gray-800">
                  Frequency of NG Events
                </h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                  <BarChart data={ruleViolations} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis 
                      type="number" 
                      stroke="#6B7280" 
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis 
                      dataKey="rule" 
                      type="category" 
                      stroke="#6B7280" 
                      width={100}
                      tick={{ fontSize: 16 }}
                    />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: "#FFFFFF", 
                        border: "1px solid #E5E7EB",
                        fontSize: "12px",
                        color: "#000000"
                      }}
                    />
                    <Bar dataKey="count">
                      {ruleViolations.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={ruleColors[index % ruleColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 gap-3 sm:gap-4">
            {/* Monthly Summary of NG Events */}
            <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg [&_*]:outline-none [&_*:focus]:outline-none">
              <div className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 shadow-md">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3 text-gray-800">
                  Monthly Summary of NG Events
                </h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]" style={{ outline: 'none' }}>
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis 
                      dataKey="month" 
                      stroke="#6B7280" 
                      height={40}
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis 
                      stroke="#6B7280" 
                      tick={{ fontSize: 11 }}
                      width={35}
                    />
                    <Tooltip
                      contentStyle={{ 
                        backgroundColor: "#FFFFFF", 
                        border: "1px solid #E5E7EB",
                        fontSize: "12px",
                        color: "#000000"
                      }}
                      formatter={(value: number, name: string) => {
                        if (name === "Empty") return [null, null];
                        return [value, name];
                      }}
                    />
                    <Bar dataKey="empty" stackId="a" fill={ppeColors.empty} barSize={65} name="Empty" />
                    
                    {/* แสดง Bar เฉพาะที่เลือก */}
                    {visiblePPE.gloves && (
                      <Bar dataKey="gloves" stackId="a" fill={ppeColors.gloves} barSize={65} name="Gloves" />
                    )}
                    {visiblePPE.glasses && (
                      <Bar dataKey="glasses" stackId="a" fill={ppeColors.glasses} barSize={65} name="Glasses" />
                    )}
                    {visiblePPE.shirt && (
                      <Bar dataKey="shirt" stackId="a" fill={ppeColors.shirt} barSize={65} name="Shirt" />
                    )}
                  </BarChart>
                </ResponsiveContainer>

                {/* Legend */}
                <div className="flex flex-wrap justify-center gap-3 mt-3">
                  <div 
                    className="flex items-center gap-1 cursor-pointer select-none transition-opacity hover:opacity-80"
                    onClick={() => togglePPEVisibility('gloves')}
                    style={{ opacity: visiblePPE.gloves ? 1 : 0.3 }}
                  >
                    <div 
                      className="w-7 h-7 rounded" 
                      style={{
                        backgroundColor: ppeColors.gloves,
                        border: visiblePPE.gloves ? 'none' : '2px solid #9CA3AF'
                      }}
                    ></div>
                    <span className="text-xs text-gray-700">Gloves</span>
                  </div>
                  
                  <div 
                    className="flex items-center gap-1 cursor-pointer select-none transition-opacity hover:opacity-80"
                    onClick={() => togglePPEVisibility('glasses')}
                    style={{ opacity: visiblePPE.glasses ? 1 : 0.3 }}
                  >
                    <div 
                      className="w-7 h-7 rounded" 
                      style={{
                        backgroundColor: ppeColors.glasses,
                        border: visiblePPE.glasses ? 'none' : '2px solid #9CA3AF'
                      }}
                    ></div>
                    <span className="text-xs text-gray-700">Glasses</span>
                  </div>
                  
                  <div 
                    className="flex items-center gap-1 cursor-pointer select-none transition-opacity hover:opacity-80"
                    onClick={() => togglePPEVisibility('shirt')}
                    style={{ opacity: visiblePPE.shirt ? 1 : 0.3 }}
                  >
                    <div 
                      className="w-7 h-7 rounded" 
                      style={{
                        backgroundColor: ppeColors.shirt,
                        border: visiblePPE.shirt ? 'none' : '2px solid #9CA3AF'
                      }}
                    ></div>
                    <span className="text-xs text-gray-700">Shirt</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}