import { CheckCircle2 } from "lucide-react";

import { ProductPreview } from "@/features/marketing/product-preview";
import { BrandMark, FadeIn } from "@/shared/ui";

const POINTS = [
  "Answers cite the exact document and page",
  "Eligibility rules are checked one by one",
  "Says so when the answer isn't in your files",
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="grid min-h-dvh lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      {/* Form side */}
      <div className="flex flex-col px-6 py-8 sm:px-12">
        <BrandMark />
        <div className="flex flex-1 items-center justify-center py-12">
          <FadeIn className="w-full max-w-[400px]">{children}</FadeIn>
        </div>
        <p className="text-[13px] text-subtle">© {new Date().getFullYear()} Ask PSI</p>
      </div>

      {/* Brand side */}
      <div className="relative hidden overflow-hidden bg-brand-gradient text-primary-fg lg:flex lg:flex-col lg:justify-center lg:px-16 xl:px-24">
        <div className="bg-dots absolute inset-0 opacity-40" aria-hidden />
        <div className="relative max-w-lg">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight">
            Your policies, answered — and applied.
          </h2>
          <ul className="mt-6 space-y-2.5">
            {POINTS.map((p) => (
              <li key={p} className="flex items-center gap-2.5 text-[15px] text-primary-fg/85">
                <CheckCircle2 className="size-4 shrink-0" aria-hidden />{p}
              </li>
            ))}
          </ul>
          <ProductPreview className="mt-12" />
        </div>
      </div>
    </main>
  );
}
