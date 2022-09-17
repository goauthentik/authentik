import { Route } from "@goauthentik/web/elements/router/Route";
import "@goauthentik/web/user/LibraryPage";

import { html } from "lit";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), async () => html`<ak-library></ak-library>`),
    new Route(new RegExp("^/settings$"), async () => {
        await import("@goauthentik/web/user/user-settings/UserSettingsPage");
        return html`<ak-user-settings></ak-user-settings>`;
    }),
];
