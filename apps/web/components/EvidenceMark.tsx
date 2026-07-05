/**
 * The Augury Market signature mark: a loose scatter of small reading
 * ticks that resolve toward a single steadier line — evidence
 * converging into a reading. Used once, on the auth screen, kept quiet
 * everywhere else in the product.
 */
export function EvidenceMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 220 90"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      {[
        [8, 62, 14],
        [26, 48, 18],
        [46, 58, 10],
        [66, 38, 22],
        [92, 44, 14],
        [114, 30, 24],
        [142, 34, 16],
        [166, 24, 20],
        [190, 20, 14],
      ].map(([x, y, h], i) => (
        <line
          key={i}
          x1={x}
          y1={y + h}
          x2={x}
          y2={y}
          stroke={i > 5 ? "#E8A33D" : "#8A8F9C"}
          strokeWidth={i > 5 ? 2.5 : 1.5}
          strokeLinecap="round"
          opacity={0.35 + i * 0.07}
        />
      ))}
      <line x1="4" y1="76" x2="210" y2="14" stroke="#E8A33D" strokeWidth="1" opacity="0.3" strokeDasharray="1 5" />
    </svg>
  );
}
