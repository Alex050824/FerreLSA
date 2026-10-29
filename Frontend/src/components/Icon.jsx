import React from 'react';

/** Íconos SVG locales: sin librerías ni servicios externos. */
export default function Icon({
  name,
  size = 22,
  strokeWidth = 1.85,
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
    <path d="M4.5 12h15" />
    <path d="m13.5 6 6 6-6 6" />
  </>,
    shield: <>
    <path d="M12 2.5 20 6v6.1c0 5-3.4 8.4-8 9.5-4.6-1.1-8-4.5-8-9.5V6z" />
    <path d="m9 12.5 2 2 4-4" />
  </>,
    eye: <>
    <path d="M2.5 12s3.5-6.3 9.5-6.3 9.5 6.3 9.5 6.3-3.5 6.3-9.5 6.3S2.5 12 2.5 12Z" />
    <circle cx="12" cy="12" r="2.8" />
  </>,
    eyeOff: <>
    <path d="m3 3 18 18" />
    <path d="M10.6 5.8a10.7 10.7 0 0 1 1.4-.1c6 0 9.5 6.3 9.5 6.3a14 14 0 0 1-3.4 4.1" />
    <path d="M6.4 6.9A15 15 0 0 0 2.5 12s3.5 6.3 9.5 6.3a10 10 0 0 0 3-.5" />
    <path d="M10.2 10.2a2.8 2.8 0 0 0 3.6 3.6" />
  </>,
    user: <>
    <circle cx="12" cy="8" r="3.5" />
    <path d="M5.2 20a6.8 6.8 0 0 1 13.6 0" />
  </>,
    lock: <>
    <rect x="5" y="10.5" width="14" height="10.5" rx="2" />
    <path d="M8 10.5V7a4 4 0 0 1 8 0v3.5" />
  </>,
    chart: <>
    <path d="M4 20V10M10 20V6M16 20v-9M22 20V4" />
  </>,
    box: <>
    <path d="m12 2.8 9 5.1v8.2l-9 5.1-9-5.1V7.9z" />
    <path d="m3 7.9 9 5.2 9-5.2M12 13.1v8.1" />
  </>,
    receipt: <>
    <path d="M6 3.5h12v17l-3-1.5-3 1.5-3-1.5-3 1.5z" />
    <path d="M9 8h6M9 12h6M9 16h3" />
  </>,
    cart: <>
    <path d="M3 4h2l2.5 11h11L21 8H6" />
    <circle cx="9" cy="20" r="1" />
    <circle cx="18" cy="20" r="1" />
  </>,
    compass: <>
    <circle cx="12" cy="12" r="9" />
    <path d="m16 8-2.8 5.2L8 16l2.8-5.2z" />
  </>,
    target: <>
    <circle cx="12" cy="12" r="9" />
    <circle cx="12" cy="12" r="5.5" />
    <circle cx="12" cy="12" r="2" />
  </>,
    check: <path d="m5 12 4.2 4.2L19 7" />,
    info: <>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5M12 8h.01" />
  </>,
    layers: <>
    <path d="m12 3 9 5-9 5-9-5z" />
    <path d="m3 12 9 5 9-5M3 16l9 5 9-5" />
  </>,
    settings: <>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5v.2h-2.6v-.2a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H6.3v-2.6h.2a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.5v-.2H15v.2a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.5 1h.2V14h-.2a1.7 1.7 0 0 0-1.5 1z" />
  </>,
    search: <>
    <circle cx="10.8" cy="10.8" r="6.8" />
    <path d="m16 16 5 5" />
  </>,
    bell: <>
    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
  </>,
    logout: <>
    <path d="M10 17l5-5-5-5M15 12H3" />
    <path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" />
  </>
  };
  return <svg {...common}>
    {paths[name] ?? paths.layers}
  </svg>;
}
