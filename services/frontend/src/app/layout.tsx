import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "FastMedia Downloader — Videos y audio hasta 4K",
  description:
    "Analiza y descarga videos o audio en cualquier calidad: 4K, 1080p, 720p o MP3. Rápido y sin registro.",
};

export const viewport: Viewport = {
  themeColor: "#0b0b14",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${inter.variable} min-h-screen font-sans text-slate-200 antialiased`}>
        {children}
      </body>
    </html>
  );
}
