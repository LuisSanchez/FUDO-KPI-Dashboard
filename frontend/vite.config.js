import react from "@vitejs/plugin-react";
import { transformWithEsbuild } from "vite";
import { defineConfig } from "vitest/config";

function jsxInJs() {
  return {
    name: "jsx-in-js",
    enforce: "pre",
    async transform(code, id) {
      const path = id.split("?")[0];
      if (path.includes("/node_modules/") || !/\/src\/.*\.js$/.test(path)) return null;
      return transformWithEsbuild(code, path, { loader: "jsx", jsx: "automatic" });
    },
  };
}

const backend = process.env.VITE_BACKEND_URL || "http://localhost:8000";
const polling = process.env.CHOKIDAR_USEPOLLING === "true";

// Relative /api stays in the browser. Do not set axios baseURL.
export default defineConfig({
  plugins: [jsxInJs(), react()],
  // The dev-server dependency scan parses entries with esbuild before plugins run.
  optimizeDeps: {
    esbuildOptions: {
      loader: { ".js": "jsx" },
      jsx: "automatic",
    },
  },
  server: {
    host: true,
    port: 3000,
    strictPort: true,
    proxy: {
      "/api": {
        target: backend,
        changeOrigin: true,
      },
    },
    watch: polling ? { usePolling: true } : undefined,
    hmr: polling ? { clientPort: 3000 } : undefined,
  },
  build: {
    outDir: "build",
    assetsDir: "static",
    emptyOutDir: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "text-summary"],
      include: [
        "src/utils/**/*.{js,jsx}",
        "src/hooks/**/*.{js,jsx}",
        "src/api/**/*.{js,jsx}",
        "src/pages/**/*.{js,jsx}",
        "src/theme.js",
        "src/ColorModeContext.js",
      ],
      exclude: ["src/**/__tests__/**", "src/**/*.test.{js,jsx}"],
      thresholds: {
        statements: 75,
        branches: 70,
        functions: 75,
        lines: 75,
      },
    },
  },
});
