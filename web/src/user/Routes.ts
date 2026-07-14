import "#user/LibraryPage/ak-library";

import { Route } from "#elements/router/core/Route";

import { html } from "lit";

/**
 * The user interface's default path. The outlet replace-redirects `/` here.
 */
export const DEFAULT_PATH = "/library";

/**
 * The user interface route table.
 *
 * Route names are stable identifiers used for Sentry span naming.
 */
export const ROUTES: Route[] = [
    new Route("/library", () => html`<ak-library></ak-library>`, "library"),
    new Route(
        "/settings",
        async () => {
            await import("#user/user-settings/UserSettingsPage");

            return html`<ak-user-settings></ak-user-settings>`;
        },
        "settings",
    ),
];
