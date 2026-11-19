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
        var __dirname: string;
    }
}

declare module "timers" {
    /**
     * Mirrors the private helper of the same purpose in `@types/node`.
     */
    type OptionalVoidArgs<TArgs extends any[]> = [void] extends TArgs ? Partial<TArgs> : TArgs;

    global {
        // `@types/node` is always in the program, and its timers return `Timeout`.
        // Browser code stores timer IDs as numbers, so prefer the DOM return type.
        function setTimeout<TArgs extends any[]>(
            callback: (...args: TArgs) => void,
            delay?: number,
            ...args: OptionalVoidArgs<TArgs>
        ): number;

        function setInterval<TArgs extends any[]>(
            callback: (...args: TArgs) => void,
            delay?: number,
            ...args: OptionalVoidArgs<TArgs>
        ): number;
    }
}

declare module "process" {
    import { Level } from "pino";

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
                 * Whether or not we are running on a CI server.
                 */
                readonly CI?: string;

                /**
                 * The application log level.
                 */
                readonly AK_LOG_LEVEL?: Level;

                /**
                 * The base URL of web server to run the tests against.
                 *
                 * Typically this is `http://localhost:9000`.
                 *
                 * @format url
                 */
                readonly AK_TEST_RUNNER_PAGE_URL?: string;

                /**
                 * @deprecated
                 * @todo Determine where this is used and if it is needed,
                 * give it a better name.
                 */
                readonly AK_API_BASE_PATH?: string;
            }
        }
    }
}
