import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "unocss/vite";
// import { compression, defineAlgorithm } from "vite-plugin-compression2";
import path from "node:path";
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
    base: process.env.TAURI_ENV_PLATFORM ? "" : "/",
    plugins: [
        vue(),
        UnoCSS(),
        // compression({
        //     algorithms: ["gzip", "brotliCompress", defineAlgorithm("deflate", { level: 9 })],
        // }),
    ],

    // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
    //
    // 1. prevent Vite from obscuring rust errors
    clearScreen: false,
    // 2. tauri expects a fixed port, fail if that port is not available
    server: {
        port: 1420,
        strictPort: true,
        host: host || false,
        hmr: host
            ? {
                  protocol: "ws",
                  host,
                  port: 1421,
              }
            : undefined,
        watch: {
            // 3. tell Vite to ignore watching `src-tauri`
            ignored: ["**/src-tauri/**"],
        },
    },
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "src"),
        },
    },
    build: {
        sourcemap: false,
        chunkSizeWarningLimit: 1000,
        rollupOptions: {
            output: {
                manualChunks(id: string) {
                    if (id.includes("node_modules")) {
                        if (id.includes("naive-ui")) return "vendor_naive_ui";
                        if (id.includes("highlight.js")) return "vendor_highlightjs";
                        // ensure both the `vue` package and any `@vue/*` helpers stay together
                        if (/node_modules\/(vue|@vue)/.test(id)) return "vendor_vue";
                        return "vendor";
                    }
                },
            },
        },
    },
}));
