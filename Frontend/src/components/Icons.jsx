import React from 'react';

/** Lightweight inline SVGs so the landing page doesn't depend on an icon library. */
export default function Icon({
  name,
  size = 24,
  strokeWidth = 1.8,
  className = ''
}) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    className,
    'aria-hidden': true
  };
  const paths = {
    arrow: <>
    <path d="M5 12h14" />
    <path d="m13 6 6 6-6 6" />
  </>,
    upRight: <>
    <path d="M7 17 17 7" />
    <path d="M8 7h9v9" />
  </>,
    check: <>
    <path d="m5 12 4.5 4.5L19 7" />
  </>,
    menu: <>
    <path d="M4 7h16M4 12h16M4 17h16" />
  </>,
    close: <>
    <path d="M5 5l14 14M19 5 5 19" />
  </>,
    tools: <>
    <path d="M14.5 6.4a4.8 4.8 0 0 0 4.9 6l-8.8 8.8a2.1 2.1 0 0 1-3-3l8.8-8.8a4.8 4.8 0 0 0 6-4.9l-3 3-3.1-.8-.8-3.1z" />
    <path d="m3.1 3.3 4.4 4.4M5.2 2.3l3.9 3.9" />
  </>,
    paint: <>
    <path d="M5 5h14v6H5z" />
    <path d="M8 11v8a2 2 0 0 0 4 0v-4" />
    <path d="M19 6.5h1.5v3H19" />
    <path d="M8 7.5h7" />
  </>,
    electricity: <path d="m13 2-9 12h7l-1 8 10-13h-7l.1-7z" />,
    plumbing: <>
    <path d="M4 4v6h5v4h6v6h5" />
    <path d="M2 4h4M2 10h4M18 18h4M18 22h4" />
    <path d="M9 8v8M15 12v4" />
  </>,
    building: <>
    <path d="M3 20h18M4 20V9l7-4 9 4v11" />
    <path d="M4 11h16M8 11v9M16 11v9M8 15h8" />
  </>,
    supplies: <>
    <path d="m12 3 9 5-9 5-9-5z" />
    <path d="m3 8 9 5 9-5M3 8v9l9 5 9-5V8" />
    <path d="M12 13v9" />
  </>,
    heart: <>
    <path d="M20.8 5.9a5.3 5.3 0 0 0-7.5 0L12 7.2l-1.3-1.3a5.3 5.3 0 0 0-7.5 7.5L12 22l8.8-8.6a5.3 5.3 0 0 0 0-7.5z" transform="translate(0 -1) scale(.96)" />
  </>,
    compass: <>
    <circle cx="12" cy="12" r="9" />
    <path d="m16 8-2.5 5.5L8 16l2.5-5.5z" />
  </>,
    shield: <>
    <path d="m12 2 8 4v6c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6z" />
    <path d="m9 12 2 2 4-4" />
  </>,
    chart: <>
    <path d="M3 20h18M6 17v-6M12 17V6M18 17v-9" />
  </>,
    star: <>
    <path d="m12 2 3.1 6.4 7 .9-5 4.9 1.2 7-6.3-3.4-6.3 3.4 1.2-7-5-4.9 7-.9z" />
  </>,
    quote: <>
    <path d="M10 11H5V7h5v5a5 5 0 0 1-5 5M20 11h-5V7h5v5a5 5 0 0 1-5 5" />
  </>,
    sparkle: <>
    <path d="m12 3 1.8 6.2L20 11l-6.2 1.8L12 19l-1.8-6.2L4 11l6.2-1.8z" />
    <path d="M19 18v4M17 20h4M5 2v3M3.5 3.5h3" />
  </>
  };
  return <svg {...common}>
    {paths[name] || paths.tools}
  </svg>;
}
