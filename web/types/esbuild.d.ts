/**
 * @file Import meta environment variables available via ESBuild.
 */

export {};
declare global {
    interface ESBuildImportEnv {
        /**
         * The authentik version injected by ESBuild during build time.
         *
         * @format semver
         */
        readonly AK_VERSION: string;

        /**
         * @todo Determine where this is used and if it is needed,
         * give it a better name.
         * @deprecated
         */
        readonly AK_API_BASE_PATH: string;
    }

    type ESBuildImportEnvKey = keyof ESBuildImportEnv;

    /**
     * Environment variables injected by ESBuild.
     */
    interface ImportMetaEnv extends ESBuildImportEnv {
        /**
         * An environment variable used to determine
         * whether Node.js is running in production mode.
         */
        readonly NODE_ENV: "development" | "production";
    }

    interface ImportMeta {
        readonly env: ImportMetaEnv;
    }
}
