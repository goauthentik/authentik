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
            }
        }
    }
}
