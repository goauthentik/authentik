/**
 * @file Import meta environment variables available via ESBuild.
 */

export {};
declare global {
    /**
     * Environment variables injected by ESBuild.
     */
    interface ImportMetaEnv {
        /**
         * The injected watcher URL for ESBuild.
         * This is used for live reloading in development mode.
         *
         * @format url
         */
        readonly ESBUILD_WATCHER_URL?: string;
    }

    interface ImportMeta {
        readonly env: ImportMetaEnv;
    }
}
