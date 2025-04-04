import { Route } from "@goauthentik/elements/router/Route";
import "@goauthentik/user/LibraryPage/ak-library.js";

import { html } from "lit";

export const ROUTES = [
    // Prevent infinite Shell loops
    Route.redirect("^/$", "/library"),
    Route.redirect("^#.*", "/library"),
    new Route("/library", async () => html`<ak-library></ak-library>`),
    new Route("/settings", async () => {
        await import("@goauthentik/user/user-settings/UserSettingsPage");

        return html`<ak-user-settings></ak-user-settings>`;
    }),
] satisfies Route<never>[];
