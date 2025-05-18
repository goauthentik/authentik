/**
 * @file Environment variables available via ESBuild.
 */

declare module "module" {
    global {
        /**
         * @deprecated This is not present in ESM files.
         *
         * ```js
         * import { dirname } from "node:path";
         * import { fileURLToPath } from "node:url";
         *
         * const relativeDirname = dirname(fileURLToPath(import.meta.url));
         * ```
         */
        // eslint-disable-next-line no-var
        var __dirname: string;
    }
}

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                CWD: string;
                /**
                 * @todo Determine where this is used and if it is needed,
                 * give it a better name.
                 * @deprecated
                 */
                AK_API_BASE_PATH: string;
            }
        }
    }
}
