import React from "react";

interface GarudaLogoProps extends React.SVGProps<SVGSVGElement> {
  size?: number | string;
  showWordmark?: boolean;
  wordmarkClassName?: string;
  subtitle?: string;
}

export function GarudaLogo({
  size = 32,
  showWordmark = false,
  wordmarkClassName = "",
  subtitle,
  className = "",
  ...props
}: GarudaLogoProps) {
  const icon = (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="GARUDA Logo"
      {...props}
    >
      <defs>
        {/* Subtle high-tech gradient: Electric Blue to Cyan */}
        <linearGradient id="garuda-primary-grad" x1="6" y1="4" x2="42" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#22D3EE" />
        </linearGradient>
        <linearGradient id="garuda-dark-wing" x1="10" y1="8" x2="24" y2="38" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1E3A8A" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>
      </defs>

      {/* Outer Hexagonal Shield Baseline */}
      <path
        d="M24 3L42 11V25C42 34.5 34.5 42.5 24 45C13.5 42.5 6 34.5 6 25V11L24 3Z"
        stroke="rgba(148, 163, 184, 0.2)"
        strokeWidth="1.5"
        strokeLinejoin="round"
        fill="rgba(13, 20, 36, 0.4)"
      />

      {/* Left Wing Facet 1 (Lower Outer) */}
      <path
        d="M10 16L22 26L14 31L9 22L10 16Z"
        fill="url(#garuda-dark-wing)"
        fillOpacity="0.8"
      />

      {/* Right Wing Facet 1 (Lower Outer) */}
      <path
        d="M38 16L26 26L34 31L39 22L38 16Z"
        fill="url(#garuda-dark-wing)"
        fillOpacity="0.8"
      />

      {/* Left Primary Wing Feathers */}
      <path
        d="M12 13L24 23L16 27L10 19L12 13Z"
        fill="url(#garuda-primary-grad)"
      />

      {/* Right Primary Wing Feathers */}
      <path
        d="M36 13L24 23L32 27L38 19L36 13Z"
        fill="url(#garuda-primary-grad)"
      />

      {/* Eagle Head & Central Crest */}
      <path
        d="M24 7L27.5 14L30 18L24 22L18 18L20.5 14L24 7Z"
        fill="#FFFFFF"
      />

      {/* Eagle Beak & Downward Strike Apex */}
      <path
        d="M24 18L26.5 24L24 28L21.5 24L24 18Z"
        fill="#22D3EE"
      />

      {/* Lower Tail / Shield Core Chevron */}
      <path
        d="M24 30L29 35L24 39L19 35L24 30Z"
        fill="#3B82F6"
        fillOpacity="0.9"
      />

      {/* Vigilant Center Dot */}
      <circle cx="24" cy="14" r="1.5" fill="#070B14" />
    </svg>
  );

  if (!showWordmark) {
    return icon;
  }

  return (
    <div className="flex items-center gap-2.5">
      {icon}
      <div className="flex flex-col">
        <span
          className={`font-mono font-bold tracking-wider text-white text-base leading-none ${wordmarkClassName}`}
        >
          GARUDA
        </span>
        {subtitle && (
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground font-sans mt-0.5">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
}
