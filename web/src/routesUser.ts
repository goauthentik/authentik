import { html } from "lit-html";
import { Route } from "./elements/router/Route";

import "./user/LibraryPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), html`<ak-library></ak-library>`),
    new Route(new RegExp("^/user$"), html`<ak-user-settings></ak-user-settings>`),
];
