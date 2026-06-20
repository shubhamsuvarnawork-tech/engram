import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";
import { EngramMark } from "@/components/logo";

export const metadata = {
  title: "Engram",
  description: "Organizational memory, made executable.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://api.fontshare.com" crossOrigin="anonymous" />
        <link href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
        <div className="min-h-screen">
          <header className="sticky top-0 z-30 border-b border-white/10 bg-[#0a0b14]/85 backdrop-blur-xl">
            <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
              <Link href="/app" className="flex items-center gap-2 font-display text-[17px] font-semibold tracking-tight text-white">
                <EngramMark className="h-6 w-6" />
                <span>Engram</span>
              </Link>
              <nav className="flex gap-5 text-sm text-slate-400">
                <Link href="/app" className="transition hover:text-white">Dashboard</Link>
                <Link href="/executions" className="transition hover:text-white">Executions</Link>
                <Link href="/docs" className="transition hover:text-white">Docs</Link>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
