// The Engram mark: a synaptic path where knowledge branches into a decision
// and one node fires into action.
export function EngramMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} role="img" aria-label="Engram">
      <g fill="none" stroke="#4F46E5" strokeWidth={2.6} strokeLinecap="round">
        <path d="M18 32 L33 19" /><path d="M18 32 L33 45" />
        <path d="M33 19 L48 32" /><path d="M33 45 L48 32" />
      </g>
      <circle cx={48} cy={32} r={9} fill="#22D3EE" opacity={0.16} />
      <circle cx={18} cy={32} r={5.6} fill="#4F46E5" />
      <circle cx={33} cy={19} r={3.8} fill="#7C3AED" />
      <circle cx={33} cy={45} r={3.8} fill="#7C3AED" />
      <circle cx={48} cy={32} r={5.6} fill="#22D3EE" />
      <circle cx={48} cy={32} r={2.1} fill="#ffffff" />
    </svg>
  );
}
