import { RawRoute, makeRoute } from "@goauthentik/elements/router/routeUtils";
import "@goauthentik/user/LibraryPage/LibraryPage";

import { html } from "lit";

export const _ROUTES: RawRoute[] = [
    // Prevent infinite Shell loops
    ["^/$", "/library"],
    ["^#.*", "/library"],
    ["^/library$", async () => html`<ak-library></ak-library>`],
    [
        "^/settings$",
        async () => {
            await import("@goauthentik/user/user-settings/UserSettingsPage");
            return html`<ak-user-settings></ak-user-settings>`;
        },
    ],
];

export const ROUTES = _ROUTES.map(makeRoute);
