import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./apiError";
import { runAnalysis } from "./analysisRun";
import type { ParamRegistry } from "../types/params";

function stubFetchOnce(resp: Partial<Response> & { ok: boolean; status: number }) {
  const fetchMock = vi.fn().mockResolvedValue(resp as Response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("runAnalysis", () => {
  it("sends effective params (value wins, otherwise default) and omits missing", async () => {
    const params: ParamRegistry = {
      // numeric: uses default
      a: {
        key: "a",
        name: "a",
        paramType: "static",
        editable: true,
        valueType: "number",
        unit: "-",
        min: 0,
        max: 10,
        default: 2,
      },
      // numeric: uses explicit value
      b: {
        key: "b",
        name: "b",
        paramType: "static",
        editable: true,
        valueType: "number",
        unit: "-",
        min: 0,
        max: 10,
        default: 2,
        value: 9,
      },
      // string: uses explicit value
      s: {
        key: "s",
        name: "s",
        paramType: "static",
        editable: true,
        valueType: "string",
        default: "d",
        value: "v",
      },
      // missing both -> omitted
      m: {
        key: "m",
        name: "m",
        paramType: "static",
        editable: true,
        valueType: "string",
      },
    };

    const fetchMock = stubFetchOnce({
      ok: true,
      status: 200,
      json: async () => ({
        results: { status: "ok", ates_kpi_results: [], derived_quantities: [] },
      }),
    });

    await runAnalysis({
      pos: { lat: 47, lng: 8 },
      params,
      runId: 123,
      startedAt: 111,
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [_url, init] = fetchMock.mock.calls[0]!;
    expect(_url).toBe("/api/analysis/run");
    expect(init.method).toBe("POST");
    const body = JSON.parse(String(init.body));
    expect(body.location).toEqual({ lat: 47, lng: 8 });
    expect(body.params).toEqual({ a: 2, b: 9, s: "v" });
  });

  it("throws ApiError for non-2xx responses", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    stubFetchOnce({
      ok: false,
      status: 422,
      text: async () => "details",
    });

    await expect(
      runAnalysis({ pos: { lat: 0, lng: 0 }, params: {} as ParamRegistry }),
    ).rejects.toBeInstanceOf(ApiError);

    await expect(
      runAnalysis({ pos: { lat: 0, lng: 0 }, params: {} as ParamRegistry }),
    ).rejects.toMatchObject({ status: 422, url: "/api/analysis/run" });
  });

  it("rethrows AbortError from fetch", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new DOMException("Aborted", "AbortError"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      runAnalysis({ pos: { lat: 0, lng: 0 }, params: {} as ParamRegistry }),
    ).rejects.toMatchObject({ name: "AbortError" });
  });

  it("wraps network errors with a stable message", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("nope"));
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      runAnalysis({ pos: { lat: 0, lng: 0 }, params: {} as ParamRegistry }),
    ).rejects.toThrow("Network error while calling /api/analysis/run");
  });
});
