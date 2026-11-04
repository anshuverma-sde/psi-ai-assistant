import type { Transition, Variants } from "framer-motion";

/** Motion tokens — the single place animation timing is defined. */
export const ease = [0.22, 1, 0.36, 1] as const;

export const duration = { fast: 0.15, base: 0.24, slow: 0.4 } as const;

export const spring: Transition = { type: "spring", stiffness: 420, damping: 34, mass: 0.8 };

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: duration.base, ease } },
  exit: { opacity: 0, y: -4, transition: { duration: duration.fast, ease } },
};

export const fade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: duration.base, ease } },
  exit: { opacity: 0, transition: { duration: duration.fast, ease } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.97, y: 6 },
  show: { opacity: 1, scale: 1, y: 0, transition: spring },
  exit: { opacity: 0, scale: 0.98, transition: { duration: duration.fast, ease } },
};

export const stagger = (gap = 0.05, delay = 0): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren: gap, delayChildren: delay } },
});
