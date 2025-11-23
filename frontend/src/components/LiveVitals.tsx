import React, { useEffect, useState, useRef } from "react";
import { connectLiveState, LiveVitals as LiveVitalsType, GeminiReport } from "../ws";
import Gauge from "./Gauge";
import { motion, AnimatePresence } from "framer-motion";

const LiveVitals: React.FC = () => {
    const [vitals, setVitals] = useState<LiveVitalsType | null>(null);
    const [report, setReport] = useState<GeminiReport | null>(null);
    const [status, setStatus] = useState<string>("connecting");
    const prevPacketCount = useRef<number>(-1);

    useEffect(() => {
        const cleanup = connectLiveState({
            onMessage: (msg) => {
                if (msg.type === "live") {
                    // Aggressive reset: If packet count is low (start of session) or drops, clear report
                    if (msg.data.session_packet_count < 10 || msg.data.session_packet_count < prevPacketCount.current) {
                        setReport(null);
                    }
                    prevPacketCount.current = msg.data.session_packet_count;
                    setVitals(msg.data);
                } else if (msg.type === "final") {
                    setReport(msg.gemini_report);
                }
            },
            onStatusChange: setStatus,
        });
        return cleanup;
    }, []);

    // Mock values
    const hr = vitals?.heart_rate ?? 0;
    const resp = vitals?.breathing_rate ?? 0;

    // Only show stroke risk if report exists
    const strokeRisk = report?.stroke_probability ? report.stroke_probability * 100 : 0;

    return (
        <div className="min-h-screen bg-[#eef2f6] font-sans text-gray-800 flex overflow-hidden relative selection:bg-indigo-500/30">

            {/* Liquid Background Elements - Enhanced */}
            <div className="absolute top-[-20%] left-[-10%] w-[60vw] h-[60vw] bg-gradient-to-br from-purple-300/40 to-indigo-300/40 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-blob"></div>
            <div className="absolute top-[10%] right-[-20%] w-[50vw] h-[50vw] bg-gradient-to-br from-yellow-200/40 to-pink-200/40 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-blob animation-delay-2000"></div>
            <div className="absolute bottom-[-20%] left-[20%] w-[60vw] h-[60vw] bg-gradient-to-br from-blue-200/40 to-cyan-200/40 rounded-full mix-blend-multiply filter blur-[100px] opacity-60 animate-blob animation-delay-4000"></div>

            {/* Noise Texture Overlay */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none z-0" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")` }}></div>

            {/* Sidebar */}
            <aside className="w-72 bg-white/60 backdrop-blur-2xl border-r border-white/40 z-20 flex flex-col p-8 hidden lg:flex shadow-[0_0_40px_rgba(0,0,0,0.03)]">
                <div className="flex items-center gap-4 mb-12">
                    <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-2xl flex items-center justify-center text-white font-bold text-2xl shadow-lg shadow-indigo-500/30">
                        NS
                    </div>
                    <div>
                        <span className="text-xl font-bold text-gray-900 tracking-tight block leading-none">Neuro</span>
                        <span className="text-xl font-bold text-indigo-600 tracking-tight block leading-none">Sentry</span>
                    </div>
                </div>

                <nav className="flex-1 space-y-3">
                    {[
                        { name: 'Dashboard', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z', active: true },
                        { name: 'Patients', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z', active: false },
                        { name: 'Analytics', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z', active: false },
                        { name: 'Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z', active: false },
                    ].map((item) => (
                        <div
                            key={item.name}
                            className={`flex items-center gap-4 px-4 py-3.5 rounded-2xl cursor-pointer transition-all duration-300 group ${item.active ? 'bg-indigo-50/80 text-indigo-600 shadow-sm ring-1 ring-indigo-100' : 'text-gray-500 hover:bg-white/60 hover:text-gray-900'}`}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className={`h-6 w-6 transition-colors ${item.active ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                            </svg>
                            <span className="font-semibold text-[15px]">{item.name}</span>
                        </div>
                    ))}
                </nav>

                <div className="mt-auto">
                    <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-3xl p-6 text-white shadow-xl shadow-indigo-500/20 relative overflow-hidden group cursor-pointer">
                        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-white/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>
                        <h4 className="font-bold text-lg mb-1">Pro Plan</h4>
                        <p className="text-sm text-indigo-100 mb-4 opacity-90">Unlock advanced AI diagnostics</p>
                        <button className="w-full py-2.5 bg-white/20 backdrop-blur-md hover:bg-white/30 rounded-xl text-sm font-bold transition-all border border-white/10">Upgrade Now</button>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8 lg:p-12 overflow-y-auto z-10 scroll-smooth">
                <header className="flex justify-between items-center mb-12">
                    <div>
                        <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight mb-2">Health Overview</h1>
                        <p className="text-gray-500 font-medium text-lg">Real-time patient monitoring</p>
                    </div>

                    <div className="flex items-center gap-6">
                        <div className="bg-white/60 backdrop-blur-xl border border-white/60 px-5 py-2.5 rounded-full shadow-sm flex items-center gap-3 transition-all hover:shadow-md hover:bg-white/80">
                            <span className={`w-2.5 h-2.5 rounded-full shadow-sm ${status === 'open' ? 'bg-green-500 animate-pulse shadow-green-400/50' : 'bg-yellow-500'}`}></span>
                            <span className="text-sm font-bold text-gray-700 tracking-wide">{status === 'open' ? 'SYSTEM ONLINE' : 'CONNECTING...'}</span>
                        </div>
                        <div className="w-12 h-12 bg-white/60 backdrop-blur-xl border border-white/60 rounded-full shadow-sm flex items-center justify-center text-gray-600 cursor-pointer hover:bg-white/90 hover:scale-105 transition-all">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                        </div>
                        <div className="w-12 h-12 bg-gray-200 rounded-full overflow-hidden border-2 border-white shadow-md cursor-pointer hover:ring-4 ring-indigo-100 transition-all">
                            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="User" />
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-12 gap-8">

                    {/* Main Vitals Area */}
                    <div className="col-span-12 lg:col-span-8 space-y-8">

                        {/* Top Cards Row */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                            {/* Heart Rate Card */}
                            <motion.div
                                className="bg-white/60 backdrop-blur-2xl border border-white/60 rounded-[2.5rem] p-8 shadow-[0_20px_40px_rgba(0,0,0,0.04)] hover:shadow-[0_30px_60px_rgba(0,0,0,0.08)] transition-all duration-500 group"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 }}
                            >
                                <div className="flex justify-between items-start mb-6">
                                    <div className="flex items-center gap-4">
                                        <div className="p-3.5 bg-red-50 rounded-2xl text-red-500 shadow-inner ring-1 ring-red-100">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-gray-800">Heart Rate</h3>
                                            <p className="text-sm text-gray-500 font-medium">Beats per minute</p>
                                        </div>
                                    </div>
                                    <span className="px-4 py-1.5 bg-green-100/80 text-green-700 text-xs font-bold rounded-full border border-green-200 backdrop-blur-sm">Normal</span>
                                </div>

                                <div className="flex justify-center py-6 relative">
                                    {/* Background Glow */}
                                    <div className="absolute inset-0 bg-red-500/5 blur-[60px] rounded-full"></div>
                                    <Gauge
                                        value={hr}
                                        min={40}
                                        max={180}
                                        label=""
                                        unit="bpm"
                                        colorStart="#ef4444"
                                        colorEnd="#b91c1c"
                                        glass={true}
                                    />
                                </div>
                            </motion.div>

                            {/* Respiration Column */}
                            <div className="space-y-6 h-full">
                                {/* Respiration */}
                                <motion.div
                                    className="bg-white/60 backdrop-blur-2xl border border-white/60 rounded-[2.5rem] p-8 shadow-[0_20px_40px_rgba(0,0,0,0.04)] hover:shadow-[0_30px_60px_rgba(0,0,0,0.08)] transition-all duration-500 flex flex-col h-full justify-between group"
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.2 }}
                                >
                                    <div className="flex items-center gap-4 mb-4">
                                        <div className="p-3.5 bg-orange-50 rounded-2xl text-orange-500 shadow-inner ring-1 ring-orange-100">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold text-gray-800">Respiration</h3>
                                            <p className="text-sm text-gray-500 font-medium">Breaths per minute</p>
                                        </div>
                                    </div>

                                    <div className="flex items-baseline gap-2 mt-2 mb-8">
                                        <span className="text-6xl font-extrabold text-gray-900 tracking-tight">{Math.round(resp)}</span>
                                        <span className="text-xl text-gray-500 font-semibold mb-1">rpm</span>
                                    </div>

                                    {/* Improved Respiration Animation */}
                                    <div className="h-28 bg-gradient-to-r from-orange-50/50 to-amber-50/50 rounded-2xl overflow-hidden relative border border-orange-100/50 flex items-center justify-center shadow-inner">
                                        <svg viewBox="0 0 200 100" className="w-full h-full" preserveAspectRatio="none">
                                            <defs>
                                                <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" stopColor="#fb923c" stopOpacity="0.8" />
                                                    <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.8" />
                                                </linearGradient>
                                            </defs>
                                            <motion.path
                                                d="M0,50 C50,20 150,80 200,50"
                                                fill="none"
                                                stroke="url(#waveGradient)"
                                                strokeWidth="5"
                                                strokeLinecap="round"
                                                initial={{ pathLength: 0, opacity: 0 }}
                                                animate={{
                                                    pathLength: 1,
                                                    opacity: 1,
                                                    d: [
                                                        "M0,50 C50,30 150,70 200,50",
                                                        "M0,50 C50,70 150,30 200,50",
                                                        "M0,50 C50,30 150,70 200,50"
                                                    ]
                                                }}
                                                transition={{
                                                    pathLength: { duration: 1, ease: "easeInOut" },
                                                    d: { duration: 4, repeat: Infinity, ease: "easeInOut" }
                                                }}
                                            />
                                            <motion.path
                                                d="M0,50 C50,20 150,80 200,50"
                                                fill="none"
                                                stroke="#fdba74"
                                                strokeWidth="10"
                                                strokeLinecap="round"
                                                style={{ opacity: 0.2, filter: "blur(4px)" }}
                                                animate={{
                                                    d: [
                                                        "M0,50 C50,30 150,70 200,50",
                                                        "M0,50 C50,70 150,30 200,50",
                                                        "M0,50 C50,30 150,70 200,50"
                                                    ]
                                                }}
                                                transition={{
                                                    duration: 4, repeat: Infinity, ease: "easeInOut", delay: 0.1
                                                }}
                                            />
                                        </svg>
                                    </div>
                                </motion.div>
                            </div>
                        </div>

                    </div>

                    {/* Right Sidebar: Risk Analysis */}
                    <div className="col-span-12 lg:col-span-4 space-y-8">

                        <motion.div
                            className="bg-white/60 backdrop-blur-2xl border border-white/60 rounded-[2.5rem] p-8 shadow-[0_20px_40px_rgba(0,0,0,0.05)] h-full flex flex-col relative overflow-hidden"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.5 }}
                        >
                            <h2 className="text-2xl font-bold text-gray-800 mb-10 relative z-10">Risk Assessment</h2>

                            <div className="space-y-12 flex-1 relative z-10">
                                {/* Stroke Risk */}
                                <div className="relative">
                                    <div className="flex justify-between items-end mb-4">
                                        <span className="font-bold text-gray-600 text-lg">Stroke Risk</span>
                                        <span className="font-extrabold text-pink-600 text-2xl">{Math.round(strokeRisk)}%</span>
                                    </div>
                                    <div className="bg-white/40 rounded-3xl p-4 border border-white/50 shadow-sm">
                                        <Gauge
                                            value={strokeRisk}
                                            max={100}
                                            label=""
                                            unit=""
                                            colorStart="#ec4899"
                                            colorEnd="#be185d"
                                            glass={true}
                                            size="small"
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* AI Report Card */}
                            <AnimatePresence mode="wait">
                                {report && (
                                    <motion.div
                                        key="report"
                                        className="mt-8 bg-gradient-to-br from-[#4f46e5] to-[#7c3aed] rounded-[2rem] p-8 text-white shadow-2xl shadow-indigo-500/30 relative overflow-hidden"
                                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ type: "spring", bounce: 0.4 }}
                                    >
                                        {/* Decorative circles */}
                                        <div className="absolute top-[-30px] right-[-30px] w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
                                        <div className="absolute bottom-[-30px] left-[-30px] w-24 h-24 bg-white/10 rounded-full blur-2xl"></div>

                                        <div className="relative z-10">
                                            <div className="flex items-center gap-3 mb-4 opacity-90">
                                                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                    </svg>
                                                </div>
                                                <h3 className="font-bold text-sm uppercase tracking-widest">AI Insight</h3>
                                            </div>
                                            <p className="text-[15px] leading-relaxed opacity-95 mb-6 font-medium border-l-2 border-white/30 pl-4">{report.summary}</p>
                                            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 hover:bg-white/20 transition-colors">
                                                <p className="text-[10px] font-bold uppercase tracking-widest opacity-70 mb-2">Recommendation</p>
                                                <p className="text-sm font-semibold">{report.recommendation}</p>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    </div>

                </div>
            </main>
        </div>
    );
};

export default LiveVitals;
