/**
 * Lightweight tooltip trigger.
 *
 * Renders a small icon that shows a tooltip bubble on hover/focus.
 * The bubble is rendered into `document.body` via a React portal so it can
 * escape overflow/stacking contexts.
 *
 * Positioning:
 * - Attempts the requested `placement` first, flips to the opposite side if the
 *   bubble would overflow the viewport, then clamps within the viewport.
 * - Recomputes while open on window resize and scroll.
 */
import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

type Props = {
  /** Tooltip content to display inside the bubble. */
  tooltip: React.ReactNode;

  /** Icon size (square) in px. */
  size?: number;

  /** Font size for the bubble content (px). */
  contentFontSize?: number;

  /** Optional accessible label for the trigger. */
  ariaLabel?: string;

  /** Preferred placement; may flip if it would overflow. */
  placement?: "top" | "right" | "bottom" | "left";

  /** Optional extra class name applied to the root trigger element. */
  className?: string;

  /** Character rendered inside the icon (defaults to `i`). */
  iconChar?: string;

  /** Optional icon foreground color. */
  iconColor?: string;

  /** Optional icon background color. When set, icon is rendered as a circle. */
  iconBgColor?: string; // new: background color for the icon
};

type Coords = { top: number; left: number; placement: NonNullable<Props["placement"]> };

export default function InfoTooltip({
  tooltip,
  size = 12,
  contentFontSize = 10,
  placement = "top",
  className = "",
  iconChar = "i",
  iconColor,
  iconBgColor,
}: Props) {
  const [open, setOpen] = useState(false);
  const [coords, setCoords] = useState<Coords | null>(null);
  const id = useId();
  const rootRef = useRef<HTMLSpanElement | null>(null);
  const bubbleRef = useRef<HTMLDivElement | null>(null);

  // Position the bubble relative to the trigger in the viewport
  function computePosition(p: NonNullable<Props["placement"]>): Coords | null {
    const el = rootRef.current;
    const bubble = bubbleRef.current;
    if (!el || !bubble) return null;

    const rect = el.getBoundingClientRect();
    const bw = bubble.offsetWidth;
    const bh = bubble.offsetHeight;
    const gap = 8;

    const clamp = (val: number, min: number, max: number) => Math.min(Math.max(val, min), max);

    const within = {
      xMin: 8,
      xMax: window.innerWidth - bw - 8,
      yMin: 8,
      yMax: window.innerHeight - bh - 8,
    };

    // try requested placement first
    const calc = (pl: Coords["placement"]) => {
      switch (pl) {
        case "top":
          return { top: rect.top - bh - gap, left: rect.left + rect.width / 2 - bw / 2 };
        case "bottom":
          return { top: rect.bottom + gap, left: rect.left + rect.width / 2 - bw / 2 };
        case "left":
          return { top: rect.top + rect.height / 2 - bh / 2, left: rect.left - bw - gap };
        case "right":
        default:
          return { top: rect.top + rect.height / 2 - bh / 2, left: rect.right + gap };
      }
    };

    // compute, flip if necessary, then clamp into viewport
    let pl = p;
    let { top, left } = calc(pl);

    if (pl === "top" && top < within.yMin) {
      pl = "bottom";
      ({ top, left } = calc(pl));
    } else if (pl === "bottom" && top > within.yMax) {
      pl = "top";
      ({ top, left } = calc(pl));
    } else if (pl === "left" && left < within.xMin) {
      pl = "right";
      ({ top, left } = calc(pl));
    } else if (pl === "right" && left > within.xMax) {
      pl = "left";
      ({ top, left } = calc(pl));
    }

    top = clamp(top, within.yMin, within.yMax);
    left = clamp(left, within.xMin, within.xMax);

    return { top, left, placement: pl };
  }

  // Recompute whenever opened, on resize/scroll
  useEffect(() => {
    if (!open) return;
    const update = () => setCoords(computePosition(placement));
    update();
    window.addEventListener("resize", update, { passive: true });
    window.addEventListener("scroll", update, { passive: true });
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update);
    };
  }, [open, placement]);

  return (
    <span
      ref={rootRef}
      className={`itp-root ${className}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      tabIndex={0}
      aria-describedby={open ? id : undefined}
      role="button"
    >
      <span
        className="itp-icon"
        style={{
          width: size,
          height: size,
          fontSize: Math.max(10, size - 4),
          color: iconColor ?? undefined,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          verticalAlign: "middle",
          backgroundColor: iconBgColor ?? undefined,
          borderRadius: iconBgColor ? "50%" : undefined,
          transform: iconBgColor ? "translateY(-1px)" : undefined, // slight nudge up for visual alignment
        }}
      >
        {iconChar}
      </span>

      {open &&
        createPortal(
          <div
            id={id}
            ref={bubbleRef}
            className={`itp-bubble ${open ? "itp-open" : ""}`}
            role="tooltip"
            data-placement={coords?.placement ?? placement}
            style={{
              position: "fixed",
              top: coords?.top ?? -9999,
              left: coords?.left ?? -9999,
              fontSize: contentFontSize, // apply centralized bubble font size
            }}
          >
            {tooltip}
          </div>,
          document.body,
        )}
    </span>
  );
}
