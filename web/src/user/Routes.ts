import "#user/LibraryPage/ak-library";

import { UUID_PATTERN } from "#elements/router/core/constants";
import { Route, type RouteLike } from "#elements/router/core/Route";

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
export const ROUTES: RouteLike[] = [
    new Route("/library", () => html`<ak-library></ak-library>`, "library"),
    new Route(
        "/requests",
        async () => {
            await import("#user/requests/AccessRequestsPage");

            return html`<ak-access-requests-page></ak-access-requests-page>`;
        },
        "requests",
    ),
    new Route<{ uuid: string }>(
        `/requests/access-request/:uuid(${UUID_PATTERN})/fulfill`,
        async ({ uuid }) => {
            await import("#user/requests/AccessRequestsPage");

            return html`<ak-access-requests-page
                request-to-fulfill=${uuid}
            ></ak-access-requests-page>`;
        },
        "requests.fulfill",
    ),
    new Route(
        // The `{/*}?` tail lets the tab segment (`/settings/sessions`) resolve to
        // this route while the page stays mounted across tab changes.
        "/settings{/*}?",
        async () => {
            await import("#user/user-settings/UserSettingsPage");

            return html`<ak-user-settings></ak-user-settings>`;
        },
        "settings",
    ),
    new Route(
        "/agents",
        async () => {
            await import("#user/agents/UserAgentsPage");

            return html`<ak-user-agents-page></ak-user-agents-page>`;
        },
        "agents",
    ),
];
