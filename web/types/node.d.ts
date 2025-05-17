/**
 * @file Global variables provided by Node.js
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

        const __dirname: string;
    }
}

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                /**
                 * Node environment, if any.
                 */
                readonly NODE_ENV?: "development" | "production";
                /**
                 * @todo Determine where this is used and if it is needed,
                 * give it a better name.
                 * @deprecated
                 */
                readonly AK_API_BASE_PATH?: string;
            }
        }
    }
}
