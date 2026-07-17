import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "hfa · trading desk",
  description: "High-frequency alpha desk — Go ingest · Rust matcher · Python RL brain.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
