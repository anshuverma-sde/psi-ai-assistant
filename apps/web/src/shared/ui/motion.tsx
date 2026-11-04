"use client";

import { AnimatePresence, motion, type HTMLMotionProps } from "framer-motion";

import { fadeUp, stagger } from "@/shared/lib/motion";

export { AnimatePresence, motion };

/** Fades + lifts its children in on mount. */
export function FadeIn({ delay = 0, ...rest }: HTMLMotionProps<"div"> & { delay?: number }) {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      exit="exit"
      variants={fadeUp}
      transition={{ delay }}
      {...rest}
    />
  );
}

/** Parent that reveals its <StaggerItem> children one after another. */
export function Stagger({ gap = 0.05, delay = 0, ...rest }: HTMLMotionProps<"div"> & { gap?: number; delay?: number }) {
  return <motion.div initial="hidden" animate="show" variants={stagger(gap, delay)} {...rest} />;
}

export function StaggerItem(props: HTMLMotionProps<"div">) {
  return <motion.div variants={fadeUp} {...props} />;
}

/** List item that animates in, out, and smoothly re-flows when siblings change. */
export function MotionItem(props: HTMLMotionProps<"li">) {
  return <motion.li layout initial="hidden" animate="show" exit="exit" variants={fadeUp} {...props} />;
}
