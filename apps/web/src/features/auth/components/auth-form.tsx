"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

import { Alert, AnimatePresence, Button, TextField } from "@/shared/ui";
import { useLogin, useRegister } from "../hooks";

const COPY = {
  login: { submit: "Log in", switchText: "No account?", switchLink: "Create one", href: "/register" },
  register: { submit: "Create account", switchText: "Have an account?", switchLink: "Log in", href: "/login" },
};

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const login = useLogin();
  const register = useRegister();
  const mutation = mode === "login" ? login : register;
  const [values, setValues] = useState({ organization_name: "", email: "", password: "" });

  const fieldErrors = mutation.error?.fieldErrors ?? {};
  const formError = mutation.error && Object.keys(fieldErrors).length === 0 ? mutation.error.message : null;
  const copy = COPY[mode];

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (mode === "login") login.mutate({ email: values.email, password: values.password });
    else register.mutate(values);
  };
  const bind = (name: keyof typeof values) => ({
    name,
    value: values[name],
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => setValues((v) => ({ ...v, [name]: e.target.value })),
    error: fieldErrors[name],
  });

  return (
    <form onSubmit={onSubmit} className="space-y-5" noValidate>
      <AnimatePresence>{formError && <Alert>{formError}</Alert>}</AnimatePresence>
      {mode === "register" && (
        <TextField label="Organization" placeholder="Northbridge University" autoComplete="organization" required {...bind("organization_name")} />
      )}
      <TextField label="Email" type="email" placeholder="you@organization.com" autoComplete="email" required {...bind("email")} />
      <TextField
        label="Password"
        type="password"
        autoComplete={mode === "login" ? "current-password" : "new-password"}
        hint={mode === "register" ? "At least 8 characters." : undefined}
        required
        {...bind("password")}
      />
      <Button type="submit" size="lg" className="w-full" loading={mutation.isPending}>{copy.submit}</Button>
      <p className="pt-2 text-center text-sm text-muted">
        {copy.switchText}{" "}
        <Link href={copy.href} className="font-semibold text-primary-ink underline-offset-4 hover:underline">{copy.switchLink}</Link>
      </p>
    </form>
  );
}
