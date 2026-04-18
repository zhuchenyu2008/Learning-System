import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
var __dirname = path.dirname(fileURLToPath(import.meta.url));
function getPackageChunkName(id) {
    var _a;
    var normalized = id.split('node_modules/')[1];
    if (!normalized) {
        return undefined;
    }
    var segments = normalized.split('/');
    var packageName = ((_a = segments[0]) === null || _a === void 0 ? void 0 : _a.startsWith('@')) ? segments.slice(0, 2).join('/') : segments[0];
    return packageName === null || packageName === void 0 ? void 0 : packageName.replace('@', '').replace('/', '-');
}
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 5173,
        host: '0.0.0.0',
    },
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: './src/test/setup.ts',
        css: true,
        restoreMocks: true,
        clearMocks: true,
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: function (id) {
                    if (!id.includes('node_modules')) {
                        return undefined;
                    }
                    if (id.includes('react-router-dom')) {
                        return 'router';
                    }
                    if (id.includes('@tanstack/react-query')) {
                        return 'react-query';
                    }
                    if (id.includes('react-markdown') ||
                        id.includes('remark-gfm') ||
                        id.includes('rehype-raw') ||
                        id.includes('rehype-sanitize') ||
                        id.includes('remark-') ||
                        id.includes('rehype-') ||
                        id.includes('micromark') ||
                        id.includes('mdast') ||
                        id.includes('hast') ||
                        id.includes('unist') ||
                        id.includes('property-information')) {
                        return 'markdown';
                    }
                    if (id.includes('lucide-react')) {
                        return 'icons';
                    }
                    if (id.includes('zustand')) {
                        return 'state';
                    }
                    if (id.includes('mermaid') ||
                        id.includes('katex') ||
                        id.includes('cytoscape') ||
                        id.includes('d3') ||
                        id.includes('dagre')) {
                        return 'mermaid';
                    }
                    if (id.includes('/react/') || id.includes('react-dom') || id.includes('scheduler')) {
                        return 'react-core';
                    }
                    return getPackageChunkName(id);
                },
            },
        },
    },
});
