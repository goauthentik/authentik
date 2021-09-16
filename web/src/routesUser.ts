import { html } from "lit-html";
import { Route } from "./elements/router/Route";

import "./user/LibraryPage";
import "./user/user-settings/UserSettingsPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), html`<ak-library></ak-library>`),
    new Route(new RegExp("^/settings$"), html`<ak-user-settings></ak-user-settings>`),
];
