/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CRM_API_BASE: string;
  readonly VITE_SSE_URL: string;
  readonly VITE_DEMO_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
