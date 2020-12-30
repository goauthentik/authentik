import { html } from "lit-html";
import { Route, SLUG_REGEX } from "./elements/router/Route";

import "./pages/LibraryPage";
import "./pages/admin-overview/AdminOverviewPage";
import "./pages/applications/ApplicationListPage";
import "./pages/applications/ApplicationViewPage";
import "./pages/sources/SourceViewPage";
import "./pages/flows/FlowViewPage";
import "./pages/events/EventListPage";

export const ROUTES: Route[] = [
    // Prevent infinite Shell loops
    new Route(new RegExp("^/$")).redirect("/library"),
    new Route(new RegExp("^#.*")).redirect("/library"),
    new Route(new RegExp("^/library$"), html`<ak-library></ak-library>`),
    new Route(new RegExp("^/administration/overview$"), html`<ak-admin-overview></ak-admin-overview>`),
    new Route(new RegExp("^/applications$"), html`<ak-application-list></ak-application-list>`),
    new Route(new RegExp(`^/applications/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-application-view .args=${args}></ak-application-view>`;
    }),
    new Route(new RegExp(`^/sources/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-source-view .args=${args}></ak-source-view>`;
    }),
    new Route(new RegExp(`^/flows/(?<slug>${SLUG_REGEX})$`)).then((args) => {
        return html`<ak-flow-view .args=${args}></ak-flow-view>`;
    }),
    new Route(new RegExp("^/events$"), html`<ak-event-list></ak-event-list>`),
];
