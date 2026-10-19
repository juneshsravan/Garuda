import React, { useId } from "react";

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
  // Unique gradient ids per instance (the logo appears several times per page,
  // sometimes inside hidden containers, where shared ids can break).
  const uid = useId().replace(/:/g, "");
  const wingId = `garuda-wing-${uid}`;
  const bodyId = `garuda-body-${uid}`;

  // Simplified GARUDA eagle - same artwork as /public/brand/garuda-eagle-simplified.svg
  const icon = (
    <svg
      width={size}
      height={size}
      viewBox="0 -10 120 120"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="GARUDA Logo"
      {...props}
    >
      <defs>
        <linearGradient id={wingId} x1="64" y1="56" x2="118" y2="4" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#6D5BFF" />
          <stop offset="0.5" stopColor="#3B82F6" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
        <linearGradient id={bodyId} x1="60" y1="14" x2="60" y2="94" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#E0FAFF" />
          <stop offset="0.35" stopColor="#22D3EE" />
          <stop offset="1" stopColor="#6D5BFF" />
        </linearGradient>
      </defs>
      {/* wings */}
      <path
        d="M66.5 34 C77 24 94 13 117 5 L107 18 L115 22 L103 30 L110 35 L97 41 L102 47 L89 49 L92 56 L76 54 L68.5 51 Z"
        fill={`url(#${wingId})`}
      />
      <path
        d="M66.5 34 C77 24 94 13 117 5 L107 18 L115 22 L103 30 L110 35 L97 41 L102 47 L89 49 L92 56 L76 54 L68.5 51 Z"
        fill={`url(#${wingId})`}
        transform="matrix(-1 0 0 1 120 0)"
      />
      {/* body */}
      <path
        d="M60 25 C67.5 27 70.5 35 69.5 46 C68.5 58 65 67 62 73 L60 75 L58 73 C55 67 51.5 58 50.5 46 C49.5 35 52.5 27 60 25 Z"
        fill={`url(#${bodyId})`}
      />
      {/* tail */}
      <path d="M54.5 70 L49 89 L56 83 L60 95 L64 83 L71 89 L65.5 70 L60 76 Z" fill={`url(#${wingId})`} />
      {/* head with hooked beak */}
      <g transform="translate(60.5 25) scale(0.82) translate(-60.5 -25)">
        <path
          d="M55.5 27 C54.5 20 57.5 13.5 63 13.5 C66.5 13.5 69 15 70.5 17 L76.5 19.5 C77.5 20.2 77.6 22.6 76 24.5 L75 22.2 L69.5 23.2 C67.5 26 64 28 60 28.5 Z"
          fill="#F0FCFF"
        />
        <circle cx="65" cy="18.2" r="1.3" fill="#020711" />
      </g>
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
