import { animate } from "framer-motion";
import { useEffect, useRef, useState } from "react";

/** Counts from the previous value to `target` (from 0 on mount), easing out. */
export function useCountUp(target: number | null | undefined, delay = 0): number | null {
  const [value, setValue] = useState<number | null>(target == null ? null : 0);
  const from = useRef(0);

  useEffect(() => {
    if (target == null) {
      setValue(null);
      return;
    }
    const controls = animate(from.current, target, {
      duration: 1.1,
      delay,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => {
        from.current = v;
        setValue(v);
      },
    });
    return () => controls.stop();
  }, [target, delay]);

  return value;
}
