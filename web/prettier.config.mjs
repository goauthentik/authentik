/**
 * @file Prettier configuration for authentik.
 *
 * @import { Config as PrettierConfig } from "prettier";
 * @todo Remove after NPM Workspaces enabled.
 */
// @ts-ignore
import { AuthentikPrettierConfig } from "@goauthentik/prettier-config";

/**
 * @type {PrettierConfig}
 */
const config = {
    ...AuthentikPrettierConfig,

    importOrder: [
        // ---

        "^~#common.+",
        "^~#elements.+",
        "^~#components.+",
        "^~#user.+",
        "^~#admin.+",
        "^~#flow.+",

        "^(@goauthentik/|#)common.+",
        "^(@goauthentik/|#)elements.+",
        "^(@goauthentik/|#)components.+",
        "^(@goauthentik/|#)user.+",
        "^(@goauthentik/|#)admin.+",
        "^(@goauthentik/|#)flow.+",

        "<THIRD_PARTY_MODULES>",

        "^@goauthentik.+",
        "^(@?)lit(.*)$",
        "\\.css$",
        "^@goauthentik/api$",
        "^[./]",
    ],
    importOrderSideEffects: false,
    importOrderSeparation: true,
};

export default config;
