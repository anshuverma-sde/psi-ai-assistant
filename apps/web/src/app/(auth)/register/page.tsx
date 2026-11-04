import type { Metadata } from "next";

import { AuthForm } from "@/features/auth/components/auth-form";

export const metadata: Metadata = { title: "Create account" };

export default function RegisterPage() {
  return (
    <>
      <h1 className="text-[28px] font-semibold tracking-tight text-fg">Create your assistant</h1>
      <p className="mb-8 mt-2 text-[15px] text-muted">Upload your PDFs and get a shareable assistant in minutes.</p>
      <AuthForm mode="register" />
    </>
  );
}
