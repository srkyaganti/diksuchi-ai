import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Diksuchi AI - Next-Generation Intelligence for Defence",
  description:
    "Transform how defence forces and contractors access critical documentation. Voice-enabled, AI-powered document intelligence in 18+ Indian languages.",
  openGraph: {
    title: "Diksuchi AI - Next-Generation Intelligence for Defence",
    description:
      "Voice-enabled document intelligence platform for Indian defence forces and contractors. Speak in your language, get instant answers from technical documentation.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Diksuchi AI - Next-Generation Intelligence for Defence",
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
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
