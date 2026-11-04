import type { Metadata } from "next";

import { AuthForm } from "@/features/auth/components/auth-form";

export const metadata: Metadata = { title: "Log in" };

export default function LoginPage() {
  return (
    <>
      <h1 className="text-[28px] font-semibold tracking-tight text-fg">Welcome back</h1>
      <p className="mb-8 mt-2 text-[15px] text-muted">Log in to manage your documents and assistant.</p>
      <AuthForm mode="login" />
    </>
  );
}
