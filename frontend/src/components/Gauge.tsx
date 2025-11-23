import React from "react";
import { motion } from "framer-motion";

interface GaugeProps {
    value: number;
    min?: number;
    max?: number;
    label: string;
    unit?: string;
    colorStart?: string;
    colorEnd?: string;
    glass?: boolean;
    size?: "small" | "normal";
}

const Gauge: React.FC<GaugeProps> = ({
    value,
    min = 0,
    max = 100,
    label,
    unit = "",
    colorStart = "#4f46e5",
    colorEnd = "#9333ea",
    glass = false,
    size = "normal",
}) => {
    const normalizedValue = Math.min(Math.max((value - min) / (max - min), 0), 1);

    const radius = 80;
    const strokeWidth = size === "small" ? 12 : 16;
    const center = 100;
    const circumference = Math.PI * radius; // Half circle

    const containerClasses = glass
        ? "flex flex-col items-center justify-center relative"
        : "flex flex-col items-center justify-center p-4 bg-white rounded-3xl shadow-[0_10px_30px_rgba(0,0,0,0.08)]";

    return (
        <div className={containerClasses}>
            {label && <h3 className="text-lg font-bold text-gray-700 mb-2">{label}</h3>}

            <div className={`relative ${size === "small" ? "w-40 h-24" : "w-56 h-32"} flex flex-col items-center justify-end`}>
                <div className="relative w-full h-full overflow-hidden">
                    <svg viewBox="0 0 200 110" className="w-full h-full absolute top-0 left-0">
                        <defs>
                            <linearGradient id={`grad-${label}-${colorStart}`} x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor={colorStart} />
                                <stop offset="100%" stopColor={colorEnd} />
                            </linearGradient>
                            <filter id="glow-arc" x="-20%" y="-20%" width="140%" height="140%">
                                <feGaussianBlur stdDeviation="6" result="blur" />
                                <feComposite in="SourceGraphic" in2="blur" operator="over" />
                            </filter>
                        </defs>

                        {/* Background Arc */}
                        <path
                            d={`M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`}
                            fill="none"
                            stroke={glass ? "rgba(255,255,255,0.15)" : "#f3f4f6"}
                            strokeWidth={strokeWidth}
                            strokeLinecap="round"
                        />

                        {/* Value Arc */}
                        <motion.path
                            d={`M ${center - radius} ${center} A ${radius} ${radius} 0 0 1 ${center + radius} ${center}`}
                            fill="none"
                            stroke={`url(#grad-${label}-${colorStart})`}
                            strokeWidth={strokeWidth}
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={circumference * (1 - normalizedValue)}
                            initial={{ strokeDashoffset: circumference }}
                            animate={{ strokeDashoffset: circumference * (1 - normalizedValue) }}
                            transition={{ duration: 1.2, ease: "easeOut" }}
                            filter="url(#glow-arc)"
                        />
                    </svg>

                    {/* Value Text - Centered and prominent */}
                    <div className="absolute inset-0 flex flex-col items-center justify-end pb-2">
                        <div className="flex items-baseline">
                            <span className={`font-extrabold text-gray-800 tracking-tight ${size === "small" ? "text-3xl" : "text-5xl"}`} style={{ textShadow: "0 2px 10px rgba(0,0,0,0.05)" }}>
                                {Math.round(value)}
                            </span>
                            {unit && <span className="text-sm text-gray-500 ml-1 font-bold opacity-80">{unit}</span>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Gauge;
