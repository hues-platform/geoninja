import { describe, expect, it } from "vitest";

import { buildHttpErrorMessage, safeReadText } from "./apiError";

describe("buildHttpErrorMessage", () => {
  it("maps common HTTP codes to short messages", () => {
    expect(buildHttpErrorMessage(400, "ignored")).toBe("Bad request to backend (400).");
    expect(buildHttpErrorMessage(404, "ignored")).toBe("Backend endpoint not found (404).");
    expect(buildHttpErrorMessage(422, "ignored")).toBe("Backend rejected the request (422).");
    expect(buildHttpErrorMessage(500, "ignored")).toBe(
      "Backend error (server-side). Backend might be offline.",
    );
  });

  it("uses trimmed body text as fallback for non-special codes", () => {
    expect(buildHttpErrorMessage(418, "  hello  ")).toBe("Backend request failed (418): hello");
    expect(buildHttpErrorMessage(418, "\n\t  ")).toBe("Backend request failed (418).");
  });
});

describe("safeReadText", () => {
  it("returns response text when available", async () => {
    const resp = { text: async () => "ok" } as unknown as Response;
    await expect(safeReadText(resp)).resolves.toBe("ok");
  });

  it("returns empty string if reading fails", async () => {
    const resp = { text: async () => Promise.reject(new Error("boom")) } as unknown as Response;
    await expect(safeReadText(resp)).resolves.toBe("");
  });
});
