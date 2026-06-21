interface HeimwendeMarkProps {
  className?: string;
  size?: number;
}

export default function HeimwendeMark({ className, size = 24 }: HeimwendeMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 22 22"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <rect width="22" height="22" rx="5" fill="#2f6fed" />
      <path
        d="M11 4.5L18.5 10.5V18H14V13H8V18H3.5V10.5L11 4.5Z"
        fill="white"
      />
    </svg>
  );
}
