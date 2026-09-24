/// <reference types="vitest/config" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
// The chirp checkout is read, never written: its UI package and design tokens
// are aliased from source so the editor renders with the real components.
export const CHIRP = process.env.CHIRP_DIR ?? path.resolve(here, '../../chirp');

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      {
        find: /^@chirpcoop\/real-chicken-ui\/(.+)$/,
        replacement: path.join(CHIRP, 'packages/real-chicken-ui/src/$1'),
      },
      {
        find: /^@chirpcoop\/design-tokens$/,
        replacement: path.join(CHIRP, 'packages/design-tokens/src/index.ts'),
      },
    ],
    dedupe: ['react', 'react-dom'],
  },
  server: { fs: { allow: [here, CHIRP] } },
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup-dom.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,
  },
});
