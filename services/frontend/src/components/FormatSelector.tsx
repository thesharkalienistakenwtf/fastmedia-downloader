"use client";

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

import { Music, MonitorPlay } from "lucide-react";
import { AUDIO_FORMAT_ID, formatFileSize, type VideoFormat } from "@/lib/api";

interface FormatSelectorProps {
  formats: VideoFormat[];
  selected: VideoFormat | null;
  onSelect: (format: VideoFormat) => void;
}

export default function FormatSelector({ formats, selected, onSelect }: FormatSelectorProps) {
  if (formats.length === 0) return null;

  return (
    <section className="w-full max-w-2xl text-left" aria-label="Selector de calidad">
      <h3 className="mb-3 px-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Elige la calidad
      </h3>
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {formats.map((format) => {
          const isAudio = Boolean(format.audio_only) || format.format_id === AUDIO_FORMAT_ID;
          const isSelected =
            selected?.format_id === format.format_id &&
            Boolean(selected?.audio_only) === isAudio;
          const estimatedBytes = format.filesize_bytes ?? format.filesize_approx ?? null;
          const humanSize =
            format.filesize_human ??
            (estimatedBytes ? formatFileSize(estimatedBytes) : null);
          const sizeLabel = humanSize ? `~ ${humanSize}` : "N/A";

          return (
            <button
              key={`${isAudio ? "audio" : "video"}-${format.format_id}`}
              type="button"
              onClick={() => onSelect(format)}
              aria-pressed={isSelected}
              className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-left transition active:scale-[0.99] ${
                isSelected
                  ? "border-violet-400/70 bg-violet-500/15 shadow-lg shadow-violet-950/40"
                  : "border-white/10 bg-white/5 hover:border-violet-400/40 hover:bg-white/[0.07]"
              }`}
            >
              {isAudio ? (
                <Music className={`h-5 w-5 shrink-0 ${isSelected ? "text-violet-300" : "text-slate-400"}`} aria-hidden />
              ) : (
                <MonitorPlay className={`h-5 w-5 shrink-0 ${isSelected ? "text-violet-300" : "text-slate-400"}`} aria-hidden />
              )}
              <span className="min-w-0 flex-1 truncate font-medium text-white">{format.label}</span>
              <span className="shrink-0 font-mono text-[11px] text-slate-500">
                {[format.ext?.toUpperCase(), sizeLabel].filter(Boolean).join(" · ")}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
