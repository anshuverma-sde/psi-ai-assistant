import { Code2, FileSearch, ListChecks, ShieldCheck } from "lucide-react";

import { ProductPreview } from "@/features/marketing/product-preview";
import { BrandMark, ButtonLink, Container, Eyebrow, IconTile, Stagger, StaggerItem } from "@/shared/ui";

const FEATURES = [
  { icon: FileSearch, title: "Grounded answers", text: "Every answer cites the document and page it came from. No sources, no answer." },
  { icon: ListChecks, title: "Rules, applied", text: "Eligibility questions are split into checks and evaluated one by one — in parallel." },
  { icon: ShieldCheck, title: "Private by default", text: "Each organization's documents are isolated. Visitors see answers, never files." },
  { icon: Code2, title: "Embed anywhere", text: "A public link plus a one-line script or iframe for any website." },
];

export default function HomePage() {
  return (
    <div className="min-h-dvh">
      <header className="border-b border-border/70 bg-background/80 backdrop-blur">
        <Container className="flex h-16 items-center justify-between">
          <BrandMark />
          <div className="flex items-center gap-2">
            <ButtonLink href="/login" variant="ghost">Log in</ButtonLink>
            <ButtonLink href="/register">Get started</ButtonLink>
          </div>
        </Container>
      </header>

      <section className="relative overflow-hidden">
        <div className="bg-dots absolute inset-0 text-primary-ink opacity-30 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" aria-hidden />
        <Container className="relative grid items-center gap-16 py-20 lg:grid-cols-2 lg:py-28">
          <Stagger gap={0.08}>
            <StaggerItem><Eyebrow>AI knowledge &amp; decision assistant</Eyebrow></StaggerItem>
            <StaggerItem>
              <h1 className="mt-5 text-4xl font-semibold leading-[1.1] tracking-tight text-fg sm:text-[56px]">
                Answers from your documents. <span className="text-primary-ink">Decisions from your rules.</span>
              </h1>
            </StaggerItem>
            <StaggerItem>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">
                Upload your policy PDFs and get an assistant that cites its sources, checks eligibility condition by
                condition, and says so when it doesn&apos;t know.
              </p>
            </StaggerItem>
            <StaggerItem className="mt-10 flex flex-wrap gap-3">
              <ButtonLink href="/register" size="lg">Create your assistant</ButtonLink>
              <ButtonLink href="/login" size="lg" variant="secondary">Log in</ButtonLink>
            </StaggerItem>
          </Stagger>
          <div className="flex justify-center lg:justify-end">
            <div className="w-full max-w-md rounded-3xl border border-border bg-surface/60 p-5 shadow-lg backdrop-blur">
              <ProductPreview />
            </div>
          </div>
        </Container>
      </section>

      <Container className="py-20">
        <Stagger gap={0.07} className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map(({ icon: Icon, title, text }) => (
            <StaggerItem key={title} className="rounded-2xl border border-border bg-surface p-6 shadow-md">
              <IconTile><Icon /></IconTile>
              <h2 className="mt-5 text-base font-semibold text-fg">{title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted">{text}</p>
            </StaggerItem>
          ))}
        </Stagger>

        <div className="relative mt-20 overflow-hidden rounded-3xl bg-brand-gradient px-8 py-14 text-center text-primary-fg sm:px-16">
          <div className="bg-dots absolute inset-0 opacity-30" aria-hidden />
          <div className="relative">
            <h2 className="text-3xl font-semibold tracking-tight">Ready in minutes</h2>
            <p className="mx-auto mt-3 max-w-md text-[15px] text-primary-fg/80">
              Create an account, upload up to 10 PDFs, and share your assistant link.
            </p>
            <ButtonLink href="/register" size="lg" variant="inverse" className="mt-8">Get started — it&apos;s free</ButtonLink>
          </div>
        </div>
      </Container>
    </div>
  );
}
