import "#user/LibraryPage/ak-library";

import { Route } from "#elements/router/Route";

import { html } from "lit";

export const ROUTES = [
    // Prevent infinite Shell loops
    Route.redirect("^/$", "/library"),
    Route.redirect("^#.*", "/library"),
    new Route("^/library$", async () => html`<ak-library></ak-library>`),
    new Route("^/settings$", async () => {
        await import("#user/user-settings/UserSettingsPage");
        return html`<ak-user-settings></ak-user-settings>`;
    }),
] satisfies Route<never>[];
