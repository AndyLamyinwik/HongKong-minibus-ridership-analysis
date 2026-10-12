import { defineConfig } from "vite";

export default defineConfig({
  base: "/hong-kong-minibus-ridership-analysis/",
  build: {
    target: "es2022",
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: "zrender",
              test: /node_modules[\\/]zrender[\\/]/,
              priority: 20,
            },
            {
              name: "echarts",
              test: /node_modules[\\/]echarts[\\/]/,
              priority: 10,
            },
          ],
        },
      },
    },
  },
  server: { port: 5173, strictPort: true },
  preview: { port: 4173, strictPort: true },
});
