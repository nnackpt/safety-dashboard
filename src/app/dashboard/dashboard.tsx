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
const mockPPEStatusData = [
  { name: "OK", value: 85, color: "#10B981" },
  { name: "NG", value: 15, color: "#DC2626" },
];

const mockMonthlyData = [
  { month: "Jan", count: 45 },
  { month: "Feb", count: 52 },
  { month: "Mar", count: 38 },
  { month: "Apr", count: 63 },
  { month: "May", count: 48 },
  { month: "Jun", count: 55 },
  { month: "Jul", count: 41 },
  { month: "Aug", count: 58 },
  { month: "Sep", count: 47 },
  { month: "Oct", count: 53 },
  { month: "Nov", count: 0 },
  { month: "Dec", count: 0 },
];

const mockRuleViolations = [
  { rule: "Safety Gloves", count: 25 },
  { rule: "Safety Shoes", count: 18 },
  { rule: "Safety Glasses", count: 15 },
  { rule: "Safety Shirt", count: 5 },
];

export default function Dashboard() {
  const router = useRouter();
  const [stats, setStats] = useState({
    todayDetections: 15,
    yesterdayDetections: 12,
    totalNG: 63,
  });
  const ruleColors = ["#DC2626", "#F59E0B", "#3B82F6", "#10B981"];
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://ath-ma-wd2503:8083/api"

  // TODO: CALL API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
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
          // setMockPPEStatusData(ppeData.data);
        }

        // Fetch rule violations
        const ruleResponse = await fetch(`${API_URL}/dashboard/rule-violations`);
        const ruleData = await ruleResponse.json();
        if (ruleData.success) {
          // setMockRuleViolations(ruleData.data);
        }

        // Fetch monthly summary
        const monthlyResponse = await fetch(`${API_URL}/dashboard/monthly-summary`);
        const monthlyData = await monthlyResponse.json();
        if (monthlyData.success) {
          // setMockMonthlyData(monthlyData.data);
        }

      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      }
    };

    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

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
                <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-2 sm:mb-3">Today's PPE NG Case</h3>
                <ResponsiveContainer width="100%" height={200} className="sm:h-[220px] lg:h-[240px]">
                  <PieChart>
                    <Pie
                      data={mockPPEStatusData}
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
                      {mockPPEStatusData.map((entry, index) => (
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
                    <Bar dataKey="count">
                      {mockRuleViolations.map((entry, index) => (
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
                  <BarChart data={mockMonthlyData}>
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