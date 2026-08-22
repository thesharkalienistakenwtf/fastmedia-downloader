"use client";

import { Clapperboard, Clock, User } from "lucide-react";
import { formatDuration, type MediaInfo } from "@/lib/api";

export default function MetadataCard({ info }: { info: MediaInfo }) {
  return (
    <section className="flex w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 shadow-xl shadow-black/30 backdrop-blur sm:flex-row">
      <div className="relative aspect-video w-full shrink-0 overflow-hidden bg-black/40 sm:aspect-auto sm:w-64">
        {info.thumbnail ? (
          /* eslint-disable-next-line @next/next/no-img-element */
          <img
            src={info.thumbnail}
            alt={info.title ?? "Miniatura del video"}
            referrerPolicy="no-referrer"
            loading="lazy"
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full min-h-40 items-center justify-center">
            <Clapperboard className="h-8 w-8 text-slate-600" aria-hidden />
          </div>
        )}
      </div>
      <div className="flex min-w-0 flex-col justify-center gap-2.5 p-5 text-left">
        <h2 className="line-clamp-2 leading-snug font-semibold text-white">{info.title ?? "Sin título"}</h2>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400">
          {info.uploader && (
            <span className="inline-flex items-center gap-1.5">
              <User className="h-4 w-4" aria-hidden />
              {info.uploader}
            </span>
          )}
          <span className="inline-flex items-center gap-1.5">
            <Clock className="h-4 w-4" aria-hidden />
            {formatDuration(info.duration)}
          </span>
        </div>
      </div>
    </section>
  );
}
