import "#user/LibraryPage/ak-library";
import "#user/discover/DiscoverPage";
import "#user/agents/AgentsPage";

import { Route } from "#elements/router/Route";

import { html } from "lit";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), async () => html`<ak-library></ak-library>`),
    new Route(new RegExp("^/discover$"), async () => html`<ak-discovery></ak-discovery>`),
    new Route(new RegExp("^/agents$"), async () => html`<ak-agents></ak-agents>`),
    new Route(new RegExp("^/settings$"), async () => {
        await import("#user/user-settings/UserSettingsPage");
        return html`<ak-user-settings></ak-user-settings>`;
    }),
];
