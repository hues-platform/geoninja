/**
 * API error utilities.
 *
 * Frontend API clients in `src/api/` throw `ApiError` for non-2xx HTTP responses
 * so callers can distinguish backend errors from other exceptions.
 *
 * This module also provides small helpers for:
 * - constructing short, user-facing messages from HTTP status codes
 * - safely reading response bodies (best-effort)
 */

export class ApiError extends Error {
  readonly status: number;
  readonly url: string;
  readonly bodyText?: string;

  constructor(args: { message: string; status: number; url: string; bodyText?: string }) {
    super(args.message);
    this.name = "ApiError";
    this.status = args.status;
    this.url = args.url;
    this.bodyText = args.bodyText;
  }
}

export function buildHttpErrorMessage(status: number, bodyText: string): string {
  /**
   * Build a short message suitable for end-user display.
   *
   * The response body is used only as a fallback to avoid showing long/unsafe
   * server traces in the UI.
   */
  // Keep user-facing message short; details can still be logged elsewhere.
  if (status === 400) return "Bad request to backend (400).";
  if (status === 404) return "Backend endpoint not found (404).";
  if (status === 422) return "Backend rejected the request (422).";
  if (status >= 500) return "Backend error (server-side). Backend might be offline.";
  // Fallback
  const trimmed = bodyText.trim();
  return trimmed
    ? `Backend request failed (${status}): ${trimmed}`
    : `Backend request failed (${status}).`;
}

export async function safeReadText(resp: Response): Promise<string> {
  /** Best-effort `resp.text()` that returns an empty string on failure. */
  try {
    return await resp.text();
  } catch {
    return "";
  }
}
