import "#user/LibraryPage/ak-library";

import { Route } from "#elements/router/Route";

import { html } from "lit";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route({ pattern: new RegExp("^/$") }).redirect("/library"),
    new Route({ pattern: new RegExp("^#.*") }).redirect("/library"),
    new Route({ pattern: "/library", handler: () => html`<ak-library></ak-library>` }),
    new Route({
        pattern: "/settings",
        loader: () => import("#user/user-settings/UserSettingsPage"),
    }),
];
