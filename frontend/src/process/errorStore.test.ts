import { beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.useFakeTimers();
  vi.resetModules();
});

describe("useErrorStore", () => {
  it("pushes and auto-dismisses errors", async () => {
    const { useErrorStore } = await import("./errorStore");
    expect(useErrorStore.getState().errors).toHaveLength(0);

    const id = useErrorStore.getState().pushError("boom", { durationMs: 50 });
    expect(useErrorStore.getState().errors).toHaveLength(1);
    expect(useErrorStore.getState().errors[0]?.id).toBe(id);

    vi.advanceTimersByTime(49);
    expect(useErrorStore.getState().errors).toHaveLength(1);

    vi.advanceTimersByTime(1);
    expect(useErrorStore.getState().errors).toHaveLength(0);
  });
});
