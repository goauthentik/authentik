/**
 * @file Node.js global types and environment variables.
 */

declare module "process" {
    global {
        namespace NodeJS {
            interface ProcessEnv {
                /**
                 * The email address of the bootstrap user created when running the tests.
                 *
                 * @format email
                 */
                readonly AUTHENTIK_BOOTSTRAP_EMAIL?: string;
                /**
                 * The password of the bootstrap user created when running the tests.
                 */
                readonly AUTHENTIK_BOOTSTRAP_PASSWORD?: string;
                /**
                 * The directory where the authentik blueprints are stored.
                 */
                readonly AUTHENTIK_BLUEPRINTS_DIR?: string;
            }
        }
    }
}
