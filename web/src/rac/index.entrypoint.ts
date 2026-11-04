import { initializeLocale } from "#common/ui/locale/runtime";

// The catalog must be active before any module that calls `msg()` at module level loads.
await initializeLocale();

await import("./ak-rac");
