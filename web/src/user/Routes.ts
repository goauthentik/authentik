import "#user/LibraryPage/ak-library";

import { Route, UUID_REGEX } from "#elements/router/Route";

import { html } from "lit";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), async () => html`<ak-library></ak-library>`),
    new Route(new RegExp("^/requests$"), async () => {
        await import("#user/requests/AccessRequestsPage");
        return html`<ak-access-requests-page></ak-access-requests-page>`;
    }),
    new Route(
        new RegExp(`^/requests/access-request/(?<uuid>${UUID_REGEX})/fulfill$`),
        async (args) => {
            await import("#user/requests/AccessRequestsPage");
            return html`<ak-access-requests-page
                request-to-fulfill=${args.uuid}
            ></ak-access-requests-page>`;
        },
    ),
    new Route(new RegExp("^/settings$"), async () => {
        await import("#user/user-settings/UserSettingsPage");
        return html`<ak-user-settings></ak-user-settings>`;
    }),
    new Route(new RegExp("^/agents$"), async () => {
        await import("#user/agents/UserAgentsPage");
        return html`<ak-user-agents-page></ak-user-agents-page>`;
    }),
];
