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

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                /**
                 * The port used by the Docker Compose HTTP service.
                 */
                COMPOSE_PORT_HTTP?: string;

                /**
                 * The port used by the Docker Compose HTTPS service.
                 */
                COMPOSE_PORT_HTTPS?: string;

                /**
                 * An environment variable used to determine
                 * whether Node.js is running in production mode.
                 *
                 * @see {@link https://nodejs.org/en/learn/getting-started/nodejs-the-difference-between-development-and-production | The difference between development and production}
                 * @runtime node
                 */
                readonly NODE_ENV?: "development" | "production";

                /**
                 * The SHA hash of the current git commit.
                 *
                 * If you're developing locally and using a Dockerized development environment,
                 * Set this environment variable to `dev` to hint that the container
                 * should prefer pre-release versioning over its own.
                 */
                readonly GIT_BUILD_HASH?: string;

                /**
                 * @todo Determine where this is used and if it is needed,
                 * give it a better name.
                 * @deprecated
                 * @runtime node
                 */
                readonly AK_API_BASE_PATH?: string;
            }
        }
    }
}
