import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RedPA AI Control Center",
  description: "Operations dashboard for the RedPA AI Agentic AI Platform",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
