//  _________________________________________________________________
// /                                                                 \
// |   FastMedia Downloader - High-Performance Engine                |
// |   Architecture & Core Implementation                            |
// |                                                                 |
// |   Author: Juan Camilo Llamas Cárdenas                           |
// |   License: MIT (Free & Open Source Use)                         |
// |   Copyright (c) 2026 Juan Camilo Llamas Cárdenas                |
// \_________________________________________________________________/
//               \
//                \   /\___/\
//                   /       \
//                  |  #   #  |
//                  \  ___  /
//                   |     |
//                   |     |      __
//                   |     \_____/  \
//                   |               |
//                    \______/\_____/
//                    /      /
//                   /      /
//                  /__/   /__/

import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "FastMedia Downloader — Videos y audio hasta 4K",
  description:
    "Analiza y descarga videos o audio en cualquier calidad: 4K, 1080p, 720p o MP3. Rápido y sin registro.",
  authors: [{ name: "Juan Camilo Llamas Cárdenas" }],
  creator: "Juan Camilo Llamas Cárdenas",
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
