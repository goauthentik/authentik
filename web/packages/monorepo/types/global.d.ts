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
                NODE_ENV?: "production" | "development";
            }
        }
    }
}
