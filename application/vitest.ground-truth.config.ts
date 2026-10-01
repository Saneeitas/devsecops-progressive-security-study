import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/ground-truth/**/*.test.ts"],
    fileParallelism: false,
    hookTimeout: 30000
  }
});
