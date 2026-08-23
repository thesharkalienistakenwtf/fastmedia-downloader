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

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  Loader2,
  RotateCcw,
  Zap,
} from "lucide-react";
import FormatSelector from "@/components/FormatSelector";
import MetadataCard from "@/components/MetadataCard";
import UrlForm from "@/components/UrlForm";
import {
  analyzeUrl,
  getJobStatus,
  getFileUrl,
  startDownload,
  type JobStatus,
  type MediaInfo,
  type VideoFormat,
} from "@/lib/api";

type Phase =
  | "idle"
  | "analyzing"
  | "ready"
  | "requesting"
  | "downloading"
  | "done"
  | "error";

const PRIMARY_BUTTON =
  "inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-white transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 sm:text-base";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [info, setInfo] = useState<MediaInfo | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<VideoFormat | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);

  const resetToIdle = useCallback(() => {
    setPhase("idle");
    setErrorMessage("");
    setInfo(null);
    setSelectedFormat(null);
    setJob(null);
    setJobId(null);
  }, []);

  const handleAnalyze = useCallback(async (url: string) => {
    setPhase("analyzing");
    setErrorMessage("");
    setInfo(null);
    setSelectedFormat(null);
    try {
      const media = await analyzeUrl(url);
      setInfo(media);
      setPhase("ready");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo analizar el video");
      setPhase("error");
    }
  }, []);

  const triggerBrowserDownload = useCallback((id: string) => {
    const anchor = document.createElement("a");
    anchor.href = getFileUrl(id);
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  }, []);

  const handleDownload = useCallback(async () => {
    if (!info || !selectedFormat) return;
    setPhase("requesting");
    setErrorMessage("");
    try {
      const payload = selectedFormat.audio_only
        ? { url: info.webpage_url, audio_only: true }
        : { url: info.webpage_url, format_id: selectedFormat.format_id };
      const { job_id } = await startDownload(payload);
      setJob(null);
      setJobId(job_id);
      setPhase("downloading");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No se pudo iniciar la descarga");
      setPhase("error");
    }
  }, [info, selectedFormat]);

  useEffect(() => {
    if (phase !== "downloading" || !jobId) return;
    let cancelled = false;

    const timer = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        if (cancelled) return;
        setJob(status);
        if (status.status === "completed") {
          clearInterval(timer);
          setPhase("done");
          triggerBrowserDownload(jobId);
        } else if (status.status === "error") {
          clearInterval(timer);
          setErrorMessage(status.error || "Ocurrió un error durante el procesamiento");
          setPhase("error");
        }
      } catch {
        /* errores transitorios de red: se reintenta en el siguiente ciclo */
      }
    }, 2000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [phase, jobId, triggerBrowserDownload]);

  const isBusy = phase === "analyzing" || phase === "requesting" || phase === "downloading";

  return (
    <main className="relative mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center px-4 pb-16">
      <section className="flex w-full flex-col items-center pt-16 text-center sm:pt-24">
        <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300">
          <Zap className="h-3.5 w-3.5" aria-hidden />
          Hasta 4K · Audio MP3 · Sin registro
        </span>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
          FastMedia{" "}
          <span className="bg-gradient-to-r from-violet-400 to-cyan-300 bg-clip-text text-transparent">
            Downloader
          </span>
        </h1>
        <p className="mt-4 max-w-xl text-sm text-slate-400 sm:text-base">
          Analiza cualquier enlace y descarga video o audio exactamente en la calidad que necesitas.
        </p>
        <div className="mt-10 w-full max-w-2xl">
          <UrlForm onAnalyze={handleAnalyze} loading={phase === "analyzing"} disabled={isBusy} />
        </div>
      </section>

      <section className="mt-12 flex w-full flex-col items-center gap-6">
        {phase === "analyzing" && <AnalyzingSkeleton />}

        {(phase === "ready" || phase === "requesting") && info && (
          <>
            <MetadataCard info={info} />
            <FormatSelector
              formats={info.formats}
              selected={selectedFormat}
              onSelect={setSelectedFormat}
            />
            {selectedFormat && (
              <button
                type="button"
                onClick={handleDownload}
                disabled={phase === "requesting"}
                className={`${PRIMARY_BUTTON} bg-gradient-to-r from-violet-600 to-fuchsia-600 shadow-lg shadow-violet-600/30 hover:brightness-110`}
              >
                {phase === "requesting" ? (
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                ) : (
                  <Download className="h-5 w-5" aria-hidden />
                )}
                {phase === "requesting" ? "Preparando…" : `Descargar · ${selectedFormat.label}`}
              </button>
            )}
          </>
        )}

        {phase === "downloading" && <DownloadProgress job={job} />}

        {phase === "done" && jobId && (
          <SuccessCard
            onRedownload={() => triggerBrowserDownload(jobId)}
            onReset={resetToIdle}
          />
        )}

        {phase === "error" && (
          <ErrorCard message={errorMessage} onRetry={resetToIdle} />
        )}
      </section>

      <footer className="mt-auto pt-16 text-center text-xs leading-relaxed text-slate-600">
        Uso responsable: descarga únicamente contenido del que tengas derechos o autorización.
        <br />
        FastMedia Downloader — arquitectura de microservicios con Next.js, FastAPI, yt-dlp y FFmpeg.
      </footer>
    </main>
  );
}

function AnalyzingSkeleton() {
  return (
    <div className="w-full max-w-2xl animate-pulse" aria-busy="true" aria-label="Analizando video">
      <div className="flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 sm:flex-row">
        <div className="aspect-video w-full shrink-0 bg-white/10 sm:aspect-auto sm:w-64" />
        <div className="flex flex-1 flex-col justify-center gap-3 p-5">
          <div className="h-5 w-3/4 rounded bg-white/10" />
          <div className="h-4 w-1/2 rounded bg-white/5" />
          <div className="h-4 w-2/5 rounded bg-white/5" />
        </div>
      </div>
    </div>
  );
}

function DownloadProgress({ job }: { job: JobStatus | null }) {
  const progress = Math.max(Math.min(job?.progress ?? 0, 100), 0);
  const stageLabel =
    job?.stage === "ensamblando pistas con FFmpeg"
      ? "Ensamblando pistas con FFmpeg…"
      : job?.stage === "en cola"
        ? "En cola…"
        : "Descargando…";

  return (
    <div className="w-full max-w-2xl rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="mb-3 flex items-center justify-between gap-4 text-sm">
        <span className="inline-flex min-w-0 items-center gap-2 font-medium text-slate-200">
          <Loader2 className="h-4 w-4 shrink-0 animate-spin text-violet-400" aria-hidden />
          <span className="truncate">{stageLabel}</span>
        </span>
        <span className="shrink-0 font-mono tabular-nums text-slate-400">{progress.toFixed(0)}%</span>
      </div>
      <div
        className="h-2.5 w-full overflow-hidden rounded-full bg-white/10"
        role="progressbar"
        aria-valuenow={Math.round(progress)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400 transition-all duration-500 ease-out"
          style={{ width: `${Math.max(progress, 3)}%` }}
        />
      </div>
      {job?.title && <p className="mt-3 truncate text-xs text-slate-500">{job.title}</p>}
    </div>
  );
}

interface ResultCardProps {
  onReset: () => void;
}

function SuccessCard({ onRedownload, onReset }: { onRedownload: () => void } & ResultCardProps) {
  return (
    <div className="w-full max-w-2xl rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-8 text-center backdrop-blur">
      <CheckCircle2 className="mx-auto h-12 w-12 text-emerald-400" aria-hidden />
      <h3 className="mt-4 text-lg font-semibold text-white">¡Descarga completada!</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-400">
        Si tu navegador no inició la descarga automáticamente, puedes reintentarla aquí.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
        <button
          type="button"
          onClick={onRedownload}
          className={`${PRIMARY_BUTTON} bg-emerald-600 hover:bg-emerald-500`}
        >
          <Download className="h-5 w-5" aria-hidden />
          Descargar de nuevo
        </button>
        <button type="button" onClick={onReset} className={`${PRIMARY_BUTTON} bg-white/10 hover:bg-white/20`}>
          <RotateCcw className="h-5 w-5" aria-hidden />
          Analizar otro video
        </button>
      </div>
    </div>
  );
}

function ErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="w-full max-w-2xl rounded-2xl border border-red-400/20 bg-red-500/10 p-8 text-center backdrop-blur">
      <AlertTriangle className="mx-auto h-12 w-12 text-red-400" aria-hidden />
      <h3 className="mt-4 text-lg font-semibold text-white">Algo salió mal</h3>
      <p className="mx-auto mt-2 max-w-md break-words text-sm text-slate-300">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className={`${PRIMARY_BUTTON} mt-6 bg-white/10 hover:bg-white/20`}
      >
        <RotateCcw className="h-5 w-5" aria-hidden />
        Intentar de nuevo
      </button>
    </div>
  );
}
