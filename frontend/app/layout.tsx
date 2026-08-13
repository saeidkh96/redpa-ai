import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RedPA AI Control Plane",
  description: "Control Plane for the RedPA AI production-oriented agentic AI platform",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
