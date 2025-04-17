/**
 * @file Import meta environment variables available via ESBuild.
 */

export {};
declare global {
    interface ImportMeta {
        readonly env: {
            /**
             * The injected watcher URL for ESBuild.
             * This is used for live reloading in development mode.
             *
             * @format url
             */
            ESBUILD_WATCHER_URL: string;
        };
    }
}
