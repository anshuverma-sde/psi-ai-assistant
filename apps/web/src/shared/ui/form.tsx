"use client";

import { Eye, EyeOff } from "lucide-react";
import { forwardRef, useState, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";

import { cn } from "@/shared/lib/format";

const control = cn(
  "block w-full rounded-lg border bg-surface px-3.5 text-[15px] text-fg shadow-sm transition-[border-color,box-shadow]",
  "placeholder:text-subtle focus:outline-none focus:ring-4",
);
const tone = (invalid?: boolean) =>
  invalid ? "border-danger focus:ring-danger-soft" : "border-border hover:border-border-strong focus:border-primary-ink focus:ring-ring";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }>(
  function Input({ invalid, className, ...rest }, ref) {
    return <input ref={ref} aria-invalid={invalid || undefined} className={cn(control, "h-11", tone(invalid), className)} {...rest} />;
  },
);

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }>(
  function Textarea({ invalid, className, ...rest }, ref) {
    return <textarea ref={ref} aria-invalid={invalid || undefined} className={cn(control, "py-2.5", tone(invalid), className)} {...rest} />;
  },
);

/** Label + control + hint/error, wired up for accessibility. */
export function Field({ id, label, hint, error, children }: {
  id: string; label: string; hint?: string; error?: string; children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-fg">{label}</label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-[13px] text-danger">{error}</p>
      ) : hint ? (
        <p className="text-[13px] text-subtle">{hint}</p>
      ) : null}
    </div>
  );
}

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  name: string;
  label: string;
  error?: string;
  hint?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField({ label, error, hint, id, type, ...rest }, ref) {
  const inputId = id ?? rest.name;
  const [visible, setVisible] = useState(false);
  const isPassword = type === "password";
  return (
    <Field id={inputId} label={label} hint={hint} error={error}>
      <div className="relative">
        <Input
          ref={ref}
          id={inputId}
          type={isPassword && visible ? "text" : type}
          invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : undefined}
          className={isPassword ? "pr-11" : undefined}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            aria-label={visible ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 grid w-11 place-items-center text-subtle transition-colors hover:text-fg"
          >
            {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
          </button>
        )}
      </div>
    </Field>
  );
});
