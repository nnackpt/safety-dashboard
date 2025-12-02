"use client";

import { useState, useEffect } from "react";
// import { useRouter } from "next/navigation";
// import {
//   PieChart,
//   Pie,
//   BarChart,
//   Bar,
//   Cell,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   PieLabelRenderProps,
// } from "recharts";
import { MonthlyDataItem } from "@/Types/Dashboard";
import dynamic from "next/dynamic";
import { ApexOptions } from "apexcharts";
import { useConfig } from "@/hooks/useConfig";

const Chart = dynamic(() => import("react-apexcharts"), { ssr: false })

export default function Dashboard() {
  // const router = useRouter();
  
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
    gloves: "#A855F7",
    glasses: "#F97316",
    shirt: "#FACC15",
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

  // const togglePPEVisibility = (key: 'gloves' | 'glasses' | 'shirt') => {
  //   setVisiblePPE(prev => ({
  //     ...prev,
  //     [key]: !prev[key]
  //   }));
  // };
  
  const [loading, setLoading] = useState(true);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  const [pieChartOptions, setPieChartOptions] = useState<ApexOptions | null>(null);
  const [barChartOptions, setBarChartOptions] = useState<ApexOptions | null>(null);
  const [monthlyChartState, setMonthlyChartState] = useState<{
    series: { name: string; data: number[] }[];
    options: ApexOptions;
  } | null>(null);
  
  const ruleColors = ["#A855F7", "#F97316", "#FACC15", "#06B6D4"];
  const { config } = useConfig();
  const API_URL = config?.API_URL || "http://ath-ma-wd2503:8083/api";

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

  // Configure Pie Chart
  useEffect(() => {
    setPieChartOptions({
      chart: { type: 'pie' },
      labels: ppeStatusData.map(item => item.name),
      colors: ppeStatusData.map(item => item.color),
      legend: { 
        position: 'bottom',
        fontSize: '14px',
        fontWeight: 700
      },
      dataLabels: {
        enabled: true,
        formatter: function(val: number, opts: { seriesIndex: number; w: { config: { labels: string[] } } }) {
          return opts.w.config.labels[opts.seriesIndex] + ": " + val.toFixed(0) + "%";
        },
        style: { fontSize: '16px', fontWeight: 700 }
      },
      tooltip: {
        y: { 
          formatter: (val: number) => val.toString() 
        }
      }
    });
  }, [ppeStatusData]);

  // Configure Bar Chart (Frequency)
  useEffect(() => {
    setBarChartOptions({
      chart: { type: 'bar', height: 350, toolbar: { show: false } },
      plotOptions: {
        bar: { 
          horizontal: true,
          borderRadius: 4,
          borderRadiusApplication: 'end',
          distributed: true
        }
      },
      colors: ruleColors,
      dataLabels: { enabled: false },
      xaxis: {
        categories: ruleViolations.map(item => item.rule),
        labels: { style: { fontSize: '11px', colors: '#6B7280' } }
      },
      yaxis: {
        labels: { style: { fontSize: '16px', colors: '#6B7280' } }
      },
      grid: { strokeDashArray: 3, borderColor: '#E5E7EB' },
      legend: { show: false },
      tooltip: {
        theme: 'dark',
        style: { fontSize: '12px' },
        y: {
          formatter: function(val: number) {
            return val + ' cases';
          },
          title: {
            formatter: function() {
              return '';
            }
          }
        }
      }
    });
  }, [ruleViolations]);

  // Configure Monthly Chart
  useEffect(() => {
    interface SeriesData {
      name: string;
      data: number[];
    }

    const series: SeriesData[] = [];
    const colors: string[] = [];

    if (visiblePPE.gloves) {
      series.push({
        name: 'Gloves',
        data: monthlyData.map(item => item.gloves)
      });
      colors.push(ppeColors.gloves);
    }
    if (visiblePPE.glasses) {
      series.push({
        name: 'Glasses',
        data: monthlyData.map(item => item.glasses)
      });
      colors.push(ppeColors.glasses);
    }
    if (visiblePPE.shirt) {
      series.push({
        name: 'Shirt',
        data: monthlyData.map(item => item.shirt)
      });
      colors.push(ppeColors.shirt);
    }

    setMonthlyChartState({
      series: series,
      options: {
        chart: {
          type: 'bar',
          height: 350,
          stacked: true,
          toolbar: {
            show: false
          },
          zoom: {
            enabled: false
          }
        },
        responsive: [{
          breakpoint: 768,
          options: {
            legend: {
              position: 'bottom',
              offsetX: -10,
              offsetY: 0
            }
          }
        }],
        plotOptions: {
          bar: {
            horizontal: false,
            borderRadius: 8,
            borderRadiusApplication: 'end',
            borderRadiusWhenStacked: 'last',
            columnWidth: '65%',
            dataLabels: {
              total: {
                enabled: true,
                style: {
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#374151'
                }
              }
            }
          },
        },
        colors: colors,
        xaxis: {
          categories: monthlyData.map(item => item.month),
          labels: { 
            style: { 
              fontSize: '11px', 
              colors: '#6B7280' 
            } 
          }
        },
        yaxis: {
          labels: { 
            style: { 
              fontSize: '11px', 
              colors: '#6B7280' 
            } 
          }
        },
        grid: { 
          strokeDashArray: 3, 
          borderColor: '#E5E7EB' 
        },
        legend: {
          show: true,
          position: 'right',
          offsetY: 0,
          fontSize: '14px',
          fontWeight: 600,
          markers: {
            size: 8,
            shape: 'circle',
            offsetX: -2,
            offsetY: 0
          },
          itemMargin: {
            horizontal: 10,
            vertical: 8
          },
          onItemClick: {
            toggleDataSeries: true
          },
          onItemHover: {
            highlightDataSeries: true
          }
        },
        tooltip: {
          theme: 'dark',
          style: { fontSize: '12px' },
          y: {
            formatter: (val: number) => val.toString()
          }
        },
        dataLabels: { 
          enabled: false 
        },
        fill: {
          opacity: 1
        }
      }
    });
  }, [monthlyData, visiblePPE]);

  const CardSkeleton = () => (
    <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
      <div className="bg-gray-100 rounded-lg p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <div className="h-6 bg-gray-200 rounded w-8"></div>
          <div className="h-12 bg-gray-200 rounded w-20"></div>
        </div>
      </div>
    </div>
  );

  const ChartSkeleton = () => (
    <div className="bg-white border-2 border-gray-200 rounded-lg p-3 sm:p-4 shadow-md animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-1/3 mb-3"></div>
      <div className="h-[200px] sm:h-[220px] lg:h-[240px] bg-gray-100 rounded"></div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 to-gray-100 text-white overflow-hidden [&_*]:outline-none [&_*:focus]:outline-none">
      {/* <Navbar /> */}

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-[1800px] mx-auto p-3 sm:p-4 lg:p-6 space-y-3 sm:space-y-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 sm:gap-3 lg:gap-4">
            {isInitialLoading ? (
              <>
                <CardSkeleton />
                <CardSkeleton />
                <CardSkeleton />
              </>
            ) : (
              <>
                <div className="bg-white shadow-xl rounded-2xl p-5 sm:p-6 border border-gray-100 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex flex-col">
                    <p className="text-sm sm:text-base lg:text-lg font-semibold mb-4 text-gray-600 flex items-center gap-2">
                      <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
                      Today&apos;s Detection
                    </p>
                    <div className="bg-gradient-to-br from-rose-500 via-rose-600 to-pink-600 rounded-xl p-5 sm:p-6 shadow-lg relative overflow-hidden">
                      {/* Decorative elements */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-16 -mt-16"></div>
                      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-5 rounded-full -ml-12 -mb-12"></div>
                      
                      <div className="flex items-center justify-between relative z-10">
                        <span className="text-base sm:text-lg lg:text-xl font-semibold text-white/90">NG</span>
                        <span className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white drop-shadow-lg">
                          {stats.todayDetections}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white shadow-xl rounded-2xl p-5 sm:p-6 border border-gray-100 md:ml-2 lg:ml-4 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex flex-col">
                    <p className="text-sm sm:text-base lg:text-lg font-semibold mb-4 text-gray-600 flex items-center gap-2">
                      <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
                      Yesterday Detection
                    </p>
                    <div className="bg-gradient-to-br from-rose-500 via-rose-600 to-pink-600 rounded-xl p-5 sm:p-6 shadow-lg relative overflow-hidden">
                      {/* Decorative elements */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-16 -mt-16"></div>
                      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-5 rounded-full -ml-12 -mb-12"></div>
                      
                      <div className="flex items-center justify-between relative z-10">
                        <span className="text-base sm:text-lg lg:text-xl font-semibold text-white/90">NG</span>
                        <span className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white drop-shadow-lg">
                          {stats.yesterdayDetections}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-white shadow-xl rounded-2xl p-5 sm:p-6 border border-gray-100 md:ml-2 lg:ml-4 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                  <div className="flex flex-col">
                    <p className="text-sm sm:text-base lg:text-lg font-semibold mb-4 text-gray-600 flex items-center gap-2">
                      <span className="w-2 h-2 bg-rose-500 rounded-full animate-pulse"></span>
                      Total NG
                    </p>
                    <div className="bg-gradient-to-br from-rose-500 via-rose-600 to-pink-600 rounded-xl p-5 sm:p-6 shadow-lg relative overflow-hidden">
                      {/* Decorative elements */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-5 rounded-full -mr-16 -mt-16"></div>
                      <div className="absolute bottom-0 left-0 w-24 h-24 bg-white opacity-5 rounded-full -ml-12 -mb-12"></div>
                      
                      <div className="flex items-center justify-between relative z-10">
                        <span className="text-base sm:text-lg lg:text-xl font-semibold text-white/90">NG</span>
                        <span className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white drop-shadow-lg">
                          {stats.totalNG}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200">
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

                <div className="bg-white shadow-lg rounded-lg p-4 sm:p-5 border-2 border-gray-200 md:mr-2 lg:mr-4">
                  <div className="flex flex-col">
                    <p className="text-sm sm:text-base lg:text-lg font-semibold mb-3 text-gray-700">Total NG</p>
                    <div className="bg-gradient-to-br from-rose-500 to-rose-600 rounded-lg p-4 sm:p-5 shadow-md">
                      <div className="flex items-center justify-between">
                        <span className="text-base sm:text-lg lg:text-xl font-semibold text-white">NG</span>
                        <span className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white">{stats.totalNG}</span>
                      </div>
                    </div>
                  </div>
                </div> */}
              </>
            )}
          </div>

          {/* Charts Row 1 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4 lg:gap-6">
            {isInitialLoading ? (
              <>
                <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg">
                  <ChartSkeleton />
                </div>
                <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg">
                  <ChartSkeleton />
                </div>
              </>
            ) : (
              <>
                {/* Today's PPE NG Case */}
                <div className="bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300">
                  <div className="bg-gradient-to-br from-white to-gray-50 border border-gray-100 rounded-xl p-4 sm:p-5 shadow-md">
                    <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-3 sm:mb-4 text-gray-800 flex items-center gap-2">
                      <div className="w-1 h-6 bg-gradient-to-b from-teal-400 to-teal-600 rounded-full"></div>
                      Today&apos;s PPE NG Case
                    </h3>
                    {pieChartOptions && (
                      <div style={{ height: '240px' }}>
                        <Chart
                          options={pieChartOptions}
                          series={ppeStatusData.map(item => item.value)}
                          type="pie"
                          height="100%"
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Frequency of NG Events */}
                <div className="bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300">
                  <div className="bg-gradient-to-br from-white to-gray-50 border border-gray-100 rounded-xl p-4 sm:p-5 shadow-md">
                    <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-3 sm:mb-4 text-gray-800 flex items-center gap-2">
                      <div className="w-1 h-6 bg-gradient-to-b from-purple-400 to-purple-600 rounded-full"></div>
                      Frequency of NG Events
                    </h3>
                    {barChartOptions && (
                      <div style={{ height: '240px' }}>
                        <Chart
                          options={barChartOptions}
                          series={[{
                            data: ruleViolations.map(item => item.count)
                          }]}
                          type="bar"
                          height="100%"
                        />
                      </div>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Charts Row 2 */}
          <div className="grid grid-cols-1">
            {isInitialLoading ? (
              <div className="bg-[#FFFFFF] border-2 border-[#FFFFFF] p-3 sm:p-4 rounded-lg">
                <ChartSkeleton />
              </div>
            ) : (
              /* Monthly Summary of NG Events */
              <div className="bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 rounded-2xl shadow-xl hover:shadow-2xl transition-all duration-300">
                <div className="bg-gradient-to-br from-white to-gray-50 border border-gray-100 rounded-xl p-4 sm:p-5 shadow-md">
                  <h3 className="text-sm sm:text-base lg:text-lg font-bold mb-3 sm:mb-4 text-gray-800 flex items-center gap-2">
                    <div className="w-1 h-6 bg-gradient-to-b from-blue-400 to-blue-600 rounded-full"></div>
                    Monthly Summary of NG Events
                  </h3>
                  {monthlyChartState && (
                    <div style={{ height: '300px' }}>
                      <Chart
                        options={monthlyChartState.options}
                        series={monthlyChartState.series}
                        type="bar"
                        height="100%"
                      />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}