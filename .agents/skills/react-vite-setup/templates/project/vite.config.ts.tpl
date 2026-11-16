import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The ports are the web app spec's ({{spec_facts}}). strictPort fails loudly on a busy port instead of
// moving to one the tests, the debugger and other agents do not know (REACT_VITE_SETUP §3).
export default defineConfig({
  plugins: [react()],
  resolve: {
    // `@/` is `src/`, the same alias tsconfig.app.json declares (APP_ARCHITECTURE §1)
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: { port: {{dev_port}}, strictPort: true },
  preview: { port: {{preview_port}}, strictPort: true },
})
