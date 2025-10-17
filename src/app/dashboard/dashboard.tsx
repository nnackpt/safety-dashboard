"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, AlertTriangle, CheckCircle, Clock, TrendingUp } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieLabelRenderProps,
} from "recharts";

// Mock Data
const mockTimelineData = [
  { date: "01/10", detections: 5 },
  { date: "02/10", detections: 8 },
  { date: "03/10", detections: 3 },
  { date: "04/10", detections: 12 },
  { date: "05/10", detections: 7 },
  { date: "06/10", detections: 15 },
  { date: "07/10", detections: 6 },
];

const mockSeverityData = [
  { name: "Critical", value: 12, color: "#DC2626" },
  { name: "High", value: 25, color: "#F59E0B" },
  { name: "Medium", value: 18, color: "#FBBF24" },
  { name: "Low", value: 8, color: "#10B981" },
];

const mockLocationData = [
  { location: "Production Line A", count: 18 },
  { location: "Production Line B", count: 15 },
  { location: "Warehouse", count: 12 },
  { location: "Assembly Area", count: 8 },
];

const mockRuleViolations = [
  { rule: "Safety Gloves", count: 25 },
  { rule: "Safety Shoes", count: 18 },
  { rule: "Safety Glasses", count: 15 },
  { rule: "Safety Vest", count: 5 },
];

const mockStatusData = [
  { name: "Resolved", value: 35, color: "#10B981" },
  { name: "Pending", value: 18, color: "#F59E0B" },
  { name: "In Progress", value: 10, color: "#3B82F6" },
];

export default function Dashboard() {
  const router = useRouter();
  const [stats, setStats] = useState({
    totalDetections: 63,
    todayDetections: 15,
    activeTickets: 28,
    resolvedToday: 7,
  });

  // TODO: CALL API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // const response = await fetch(`${API_URL}/dashboard/stats`);
        // const data = await response.json();
        // setStats(data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      }
    };

    // fetchDashboardData();
    // const interval = setInterval(fetchDashboardData, 30000);
    // return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[#09304F] text-white overflow-hidden">
      {/* Header */}
      <div className="bg-[#0B4A82] px-3 sm:px-4 lg:px-6 py-2 sm:py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2 sm:gap-4">
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-1 sm:gap-2 bg-[#2F2F2F] hover:bg-[#3A3A3A] px-2 sm:px-3 py-1.5 sm:py-2 rounded transition-colors cursor-pointer text-xs sm:text-sm"
          >
            <ArrowLeft size={16} className="sm:w-5 sm:h-5" />
            <span>Back to Monitor</span>
          </button>
          <h1 className="text-base sm:text-xl lg:text-2xl font-bold">Safety Dashboard</h1>
        </div>
        <img src="/logo.png" alt="Logo" className="h-6 sm:h-8 lg:h-10" />
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[1800px] mx-auto p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 lg:gap-4">
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] sm:text-xs lg:text-sm text-gray-300">Total Detections</p>
                  <p className="text-xl sm:text-2xl lg:text-3xl font-bold mt-0.5 sm:mt-1">{stats.totalDetections}</p>
                </div>
                <AlertTriangle className="text-red-500 w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10" />
              </div>
            </div>

            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] sm:text-xs lg:text-sm text-gray-300">Today&apos;s Detections</p>
                  <p className="text-xl sm:text-2xl lg:text-3xl font-bold mt-0.5 sm:mt-1">{stats.todayDetections}</p>
                </div>
                <TrendingUp className="text-yellow-500 w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10" />
              </div>
            </div>

            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] sm:text-xs lg:text-sm text-gray-300">Active Tickets</p>
                  <p className="text-xl sm:text-2xl lg:text-3xl font-bold mt-0.5 sm:mt-1">{stats.activeTickets}</p>
                </div>
                <Clock className="text-orange-500 w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10" />
              </div>
            </div>

            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-[10px] sm:text-xs lg:text-sm text-gray-300">Resolved Today</p>
                  <p className="text-xl sm:text-2xl lg:text-3xl font-bold mt-0.5 sm:mt-1">{stats.resolvedToday}</p>
                </div>
                <CheckCircle className="text-green-500 w-6 h-6 sm:w-8 sm:h-8 lg:w-10 lg:h-10" />
              </div>
            </div>
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
            {/* Detection Timeline */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Detection Timeline (Last 7 Days)</h3>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                <LineChart data={mockTimelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#94A3B8" 
                    tick={{ fontSize: 11 }}
                    height={40}
                  />
                  <YAxis 
                    stroke="#94A3B8" 
                    tick={{ fontSize: 11 }}
                    width={35}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: "#1E293B", 
                      border: "1px solid #334155",
                      fontSize: "12px"
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px" }} />
                  <Line
                    type="monotone"
                    dataKey="detections"
                    stroke="#F59E0B"
                    strokeWidth={2}
                    dot={{ fill: "#F59E0B", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Severity Distribution */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Severity Distribution</h3>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                <PieChart>
                  <Pie
                    data={mockSeverityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: PieLabelRenderProps) => {
                      const { name, percent } = props as { name?: string; percent?: number };
                      const n = typeof name === "string" ? name : String(name ?? "");
                      const p = typeof percent === "number" ? (percent * 100).toFixed(0) : "0";
                      return `${n}: ${p}%`;
                    }}
                    outerRadius="70%"
                    fill="#8884d8"
                    dataKey="value"
                    style={{ fontSize: "11px" }}
                  >
                    {mockSeverityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: "#1E293B", 
                      border: "1px solid #334155",
                      fontSize: "12px"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
            {/* Detections by Location */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Detections by Location</h3>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                <BarChart data={mockLocationData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    dataKey="location" 
                    stroke="#94A3B8" 
                    angle={-15} 
                    textAnchor="end" 
                    height={70}
                    tick={{ fontSize: 10 }}
                  />
                  <YAxis 
                    stroke="#94A3B8" 
                    tick={{ fontSize: 11 }}
                    width={35}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: "#1E293B", 
                      border: "1px solid #334155",
                      fontSize: "12px"
                    }}
                  />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Rule Violations */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">PPE Rule Violations</h3>
              <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                <BarChart data={mockRuleViolations} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis 
                    type="number" 
                    stroke="#94A3B8" 
                    tick={{ fontSize: 11 }}
                  />
                  <YAxis 
                    dataKey="rule" 
                    type="category" 
                    stroke="#94A3B8" 
                    width={100}
                    tick={{ fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: "#1E293B", 
                      border: "1px solid #334155",
                      fontSize: "12px"
                    }}
                  />
                  <Bar dataKey="count" fill="#F59E0B" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Ticket Status */}
          <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
            <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Ticket Status Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
              <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                <PieChart>
                  <Pie
                    data={mockStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(props: PieLabelRenderProps) => {
                      const { name, percent } = props as { name?: string; percent?: number };
                      const n = typeof name === "string" ? name : String(name ?? "");
                      const p = typeof percent === "number" ? (percent * 100).toFixed(0) : "0";
                      return `${n}: ${p}%`;
                    }}
                    outerRadius="70%"
                    fill="#8884d8"
                    dataKey="value"
                    style={{ fontSize: "11px" }}
                  >
                    {mockStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ 
                      backgroundColor: "#1E293B", 
                      border: "1px solid #334155",
                      fontSize: "12px"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="flex flex-col justify-center space-y-2 sm:space-y-3">
                {mockStatusData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2 sm:gap-3">
                      <div
                        className="w-3 h-3 sm:w-4 sm:h-4 rounded"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm sm:text-base lg:text-lg">{item.name}</span>
                    </div>
                    <span className="text-xl sm:text-2xl font-bold">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}