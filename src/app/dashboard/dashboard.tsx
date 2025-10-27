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

export default function Dashboard() {
  const router = useRouter();
  
  // ✅ States สำหรับเก็บข้อมูลจาก API
  const [stats, setStats] = useState({
    todayDetections: 0,
    yesterdayDetections: 0,
    totalNG: 0,
  });
  
  const [ppeStatusData, setPpeStatusData] = useState([
    { name: "OK", value: 0, color: "#10B981" },
    { name: "NG", value: 0, color: "#DC2626" },
  ]);
  
  const [monthlyData, setMonthlyData] = useState([
    { month: "Jan", count: 0 },
    { month: "Feb", count: 0 },
    { month: "Mar", count: 0 },
    { month: "Apr", count: 0 },
    { month: "May", count: 0 },
    { month: "Jun", count: 0 },
    { month: "Jul", count: 0 },
    { month: "Aug", count: 0 },
    { month: "Sep", count: 0 },
    { month: "Oct", count: 0 },
    { month: "Nov", count: 0 },
    { month: "Dec", count: 0 },
  ]);
  
  const [ruleViolations, setRuleViolations] = useState([
    { rule: "Safety Gloves", count: 0 },
    { rule: "Safety Shoes", count: 0 },
    { rule: "Safety Glasses", count: 0 },
    { rule: "Safety Shirt", count: 0 },
  ]);
  
  const [loading, setLoading] = useState(true);
  
  const ruleColors = ["#DC2626", "#F59E0B", "#3B82F6", "#10B981"];
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
          setMonthlyData(monthlyDataResponse.data);
        }

      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [API_URL]);

  // ✅ Loading State
  if (loading) {
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
    <div className="h-screen flex flex-col bg-[#09304F] text-white overflow-hidden">
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
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3">Today&apos;s Detection</p>
                  <div className="bg-red-600 border-2 border-white rounded-lg p-3 sm:p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold">NG</span>
                      <span className="text-2xl sm:text-3xl lg:text-4xl font-bold">{stats.todayDetections}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3">Yesterday Detection</p>
                  <div className="bg-red-600 border-2 border-white rounded-lg p-3 sm:p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold">NG</span>
                      <span className="text-2xl sm:text-3xl lg:text-4xl font-bold">{stats.yesterdayDetections}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <div className="flex flex-col">
                  <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3">Total NG</p>
                  <div className="bg-red-600 border-2 border-white rounded-lg p-3 sm:p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-base sm:text-lg lg:text-xl font-semibold">NG</span>
                      <span className="text-2xl sm:text-3xl lg:text-4xl font-bold">{stats.totalNG}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
            {/* Today's PPE NG Case */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Today&apos;s PPE NG Case</h3>
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
                      outerRadius="70%"
                      fill="#8884d8"
                      dataKey="value"
                      style={{ fontSize: "11px" }}
                    >
                      {ppeStatusData.map((entry, index) => (
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

            {/* Frequency of NG Events */}
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Frequency of NG Events</h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                  <BarChart data={ruleViolations} layout="vertical">
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
            <div className="bg-[#0B4A82] border-2 border-[#005496] p-3 sm:p-4 rounded-lg">
              <div className="bg-[#09304F] border-2 border-white rounded-lg p-3 sm:p-4">
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Monthly Summary of NG Events</h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis 
                      dataKey="month" 
                      stroke="#94A3B8" 
                      height={40}
                      tick={{ fontSize: 11 }}
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}