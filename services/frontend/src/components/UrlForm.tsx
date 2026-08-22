"use client";

import { useState, type FormEvent } from "react";
import { Link2, Loader2, Search } from "lucide-react";

interface UrlFormProps {
  onAnalyze: (url: string) => void;
  loading: boolean;
  disabled?: boolean;
}

export default function UrlForm({ onAnalyze, loading, disabled }: UrlFormProps) {
  const [url, setUrl] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = url.trim();
    if (!trimmed || loading || disabled) return;
    onAnalyze(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-3 shadow-2xl shadow-violet-950/40 backdrop-blur transition-colors focus-within:border-violet-400/50 sm:flex-row sm:items-center">
        <div className="flex flex-1 items-center gap-3">
          <Link2 className="ml-1 hidden h-5 w-5 shrink-0 text-slate-500 sm:block" aria-hidden />
          <input
            type="text"
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="Pega aquí la URL del video o audio…"
            disabled={disabled}
            className="h-12 w-full bg-transparent px-2 text-base text-white placeholder:text-slate-500 outline-none disabled:opacity-60"
            aria-label="URL del video"
          />
        </div>
        <button
          type="submit"
          disabled={loading || disabled || !url.trim()}
          className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-xl bg-violet-600 px-6 text-sm font-semibold text-white shadow-lg shadow-violet-600/25 transition hover:bg-violet-500 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 sm:text-base"
        >
          {loading ? (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
          ) : (
            <Search className="h-5 w-5" aria-hidden />
          )}
          {loading ? "Analizando…" : "Analizar Video"}
        </button>
      </div>
    </form>
  );
}
