import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import "./globals.css";

export const metadata: Metadata = {
  title: "Diksuchi AI | AVision Systems",
  description:
    "Transform how defence forces and contractors access critical documentation. Voice-enabled, AI-powered document intelligence in 14 languages.",
  openGraph: {
    title: "Diksuchi AI | AVision Systems",
    description:
      "Voice-enabled document intelligence platform for Indian defence forces and contractors. Speak in your language, get instant answers from technical documentation.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Diksuchi AI | AVision Systems",
    description:
      "Voice-enabled document intelligence platform for Indian defence forces and contractors. Speak in your language, get instant answers from technical documentation.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${GeistSans.variable} ${GeistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
