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

    type ESBuildImportEnvKey = keyof ImportMetaEnv;

    interface ImportMeta {
        readonly env: ImportMetaEnv;
    }
}
