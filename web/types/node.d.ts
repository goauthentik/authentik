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
        // eslint-disable-next-line no-var
        var __dirname: string;
    }
}

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                /**
                 * An environment variable used to determine
                 * whether Node.js is running in production mode.
                 *
                 * @see {@link https://nodejs.org/en/learn/getting-started/nodejs-the-difference-between-development-and-production | The difference between development and production}
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
