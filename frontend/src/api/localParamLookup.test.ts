import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./apiError";
import { lookupLocalParams } from "./localParamLookup";
import type { Param } from "../types/params";

function stubFetchOnce(resp: Partial<Response> & { ok: boolean; status: number }) {
  const fetchMock = vi.fn().mockResolvedValue(resp as Response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("lookupLocalParams", () => {
  it("returns all requested keys, non-ok and missing results become null", async () => {
    stubFetchOnce({
      ok: true,
      status: 200,
      json: async () => ({
        results: [
          { key: "k1", status: "ok", value: 123 },
          { key: "k2", status: "error", value: 999 },
          { key: "extra", status: "ok", value: 1 },
        ],
      }),
    });

    const localParams: Param[] = [
      {
        key: "k1",
        name: "k1",
        paramType: "local",
        editable: false,
        valueType: "number",
        unit: "-",
        min: 0,
        max: 1,
      },
      {
        key: "k2",
        name: "k2",
        paramType: "local",
        editable: false,
        valueType: "string",
      },
      {
        key: "k3",
        name: "k3",
        paramType: "local",
        editable: false,
        valueType: "number",
        unit: "-",
        min: 0,
        max: 1,
      },
    ];

    const out = await lookupLocalParams({ pos: { lat: 1, lng: 2 }, localParams });
    expect(out).toEqual({ k1: 123, k2: null, k3: null });
  });

  it("throws ApiError on non-2xx responses", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    stubFetchOnce({
      ok: false,
      status: 404,
      text: async () => "not found",
    });

    await expect(
      lookupLocalParams({ pos: { lat: 0, lng: 0 }, localParams: [] }),
    ).rejects.toBeInstanceOf(ApiError);
  });
});
