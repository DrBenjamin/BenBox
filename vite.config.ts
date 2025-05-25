import { defineConfig } from 'vite';

// Vite configuration to suppress HMR overlay and limit logging
export default defineConfig({
  server: {
    hmr: {
      overlay: false  // disable error overlay in browser
    }
  },
  logLevel: 'error', // only show errors in terminal
  plugins: [
    {
      name: 'suppress-vite-internal-errors',
      configureServer(server) {
        // Suppress Vite internal abort and invalid-arg errors so requests still pass through
        server.middlewares.use((err: any, req: any, res: any, next: any) => {
          if (err && (
            (err.message && (err.message.includes('AbortSignal.abortHandler') || err.message.includes('ERR_INVALID_ARG_TYPE'))) ||
            (err.name && err.name === 'TypeError' && err.code === 'ERR_INVALID_ARG_TYPE')
          )) {
            console.warn('[vite] suppressed error');
            return next();
          }
          next(err);
        });
      }
    }
  ]
});
