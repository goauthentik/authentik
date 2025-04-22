/**
 * @file Environment variables available via ESBuild.
 */

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                NODE_ENV: "production" | "development";
                /**
                 *
                 * @todo Determine where this is used and if it is needed,
                 * give it a better name.
                 * @deprecated
                 */
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
