import { html } from "lit-html";
import { Route, SLUG_REGEX } from "./pages/router/Route";

import "./pages/LibraryPage";
import "./pages/admin-overview/AdminOverviewPage";
import "./pages/applications/ApplicationListPage";
import "./pages/applications/ApplicationViewPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library/"),
    new Route(new RegExp("^#.*")).redirect("/library/"),
    new Route(new RegExp("^/library/$"), html`<pb-library></pb-library>`),
    new Route(new RegExp("^/administration/overview-ng/$"), html`<pb-admin-overview></pb-admin-overview>`),
    new Route(new RegExp("^/applications/$"), html`<pb-application-list></pb-application-list>`),
    new Route(new RegExp(`^/applications/(?<slug>${SLUG_REGEX})/$`)).then((args) => {
        return html`<pb-application-view .args=${args}></pb-application-view>`;
    }),
];
