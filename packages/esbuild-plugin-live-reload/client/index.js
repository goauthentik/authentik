/**
 * @file Entry point for the ESBuild client-side observer.
 */
/// <reference types="./types.js" />
import { ESBuildObserver } from "./ESBuildObserver.js";

if (import.meta.env?.ESBUILD_WATCHER_URL) {
    const buildObserver = new ESBuildObserver(import.meta.env.ESBUILD_WATCHER_URL);

    window.addEventListener("beforeunload", () => {
        buildObserver.dispose();
    });
}
