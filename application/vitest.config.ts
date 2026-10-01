import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    exclude: ["tests/ground-truth/**", "node_modules/**", "dist/**"]
  }
});
