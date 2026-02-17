import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",

    // Test file patterns
    include: ["src/**/*.{test,spec}.{ts,tsx}"],

    // JUnit output for CI
    reporters: ["default", "junit"],
    outputFile: {
      junit: "junit.xml",
    },
  },
});
