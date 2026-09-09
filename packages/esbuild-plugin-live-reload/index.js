/**
 * @file Entry point for the ESBuild client-side observer.
 */

/// <reference types="./client/types.js" />

import { ESBuildObserver } from "./client/index.js";

if (import.meta.env?.ESBUILD_WATCHER_URL) {
    ESBuildObserver.initialize(import.meta.env.ESBUILD_WATCHER_URL);
}
