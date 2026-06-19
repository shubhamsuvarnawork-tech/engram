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
        <div className="min-h-screen">
          <header className="border-b bg-white">
            <div className="mx-auto flex max-w-5xl items-center gap-6 px-6 py-3">
              <Link href="/app" className="flex items-center gap-2 font-semibold">
                <EngramMark className="h-6 w-6" />
                <span className="tracking-tight">Engram</span>
              </Link>
              <nav className="flex gap-4 text-sm text-slate-600">
                <Link href="/app" className="hover:text-slate-900">Dashboard</Link>
                <Link href="/executions" className="hover:text-slate-900">Executions</Link>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-5xl px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
