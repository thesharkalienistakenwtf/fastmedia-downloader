// Cliente tipado del API Gateway de FastMedia Downloader.

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const AUDIO_FORMAT_ID = "bestaudio";

export interface VideoFormat {
  format_id: string;
  label: string;
  height?: number;
  ext?: string | null;
  filesize_approx?: number | null;
  audio_only?: boolean;
}

export interface MediaInfo {
  title: string | null;
  thumbnail: string | null;
  duration: number | null;
  uploader: string | null;
  webpage_url: string;
  formats: VideoFormat[];
}

export type JobState = "queued" | "downloading" | "processing" | "completed" | "error";

export interface JobStatus {
  job_id: string;
  status: JobState;
  progress: number;
  stage: string;
  title: string | null;
  filename: string | null;
  error: string | null;
}

async function parseResponse<T>(response: Response): Promise<T> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    /* cuerpo vacio o no JSON */
  }
  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String((body as { detail?: unknown }).detail)
        : `Error ${response.status}`;
    throw new Error(detail);
  }
  return body as T;
}

export async function analyzeUrl(url: string): Promise<MediaInfo> {
  return parseResponse(
    await fetch(`${API_BASE}/api/v1/info?url=${encodeURIComponent(url)}`, { cache: "no-store" })
  );
}

export interface StartDownloadPayload {
  url: string;
  format_id?: string;
  audio_only?: boolean;
}

export async function startDownload(payload: StartDownloadPayload): Promise<{ job_id: string }> {
  return parseResponse(
    await fetch(`${API_BASE}/api/v1/downloads`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  return parseResponse(await fetch(`${API_BASE}/api/v1/downloads/${jobId}`, { cache: "no-store" }));
}

export function getFileUrl(jobId: string): string {
  return `${API_BASE}/api/v1/downloads/${jobId}/file`;
}

export function formatDuration(totalSeconds: number | null): string {
  if (!totalSeconds || totalSeconds < 0) return "--:--";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = Math.floor(totalSeconds % 60);
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) return "";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 100 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}
