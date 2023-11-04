import "@goauthentik/app/common/oauth/callback";
import "@goauthentik/app/common/oauth/signout";
import { Route } from "@goauthentik/elements/router/Route";
import "@goauthentik/user/LibraryPage/LibraryPage";

import { html } from "lit";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/oauth-callback/(?<rest>.*)$"), async (args) => {
        return html`<ak-oauth-callback params=${args.rest}></ak-oauth-callback>`;
    }),
    new Route(new RegExp("^/oauth-signout$"), async () => {
        return html`<ak-oauth-signout></ak-oauth-signout>`;
    }),
    new Route(new RegExp("^/library$"), async () => html`<ak-library></ak-library>`),
    new Route(new RegExp("^/settings$"), async () => {
        await import("@goauthentik/user/user-settings/UserSettingsPage");
        return html`<ak-user-settings></ak-user-settings>`;
    }),
];
