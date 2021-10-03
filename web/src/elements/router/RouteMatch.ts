import { TemplateResult } from "lit";

import { Route } from "./Route";

export class RouteMatch {
    route: Route;
    arguments: { [key: string]: string };
    fullUrl?: string;

    constructor(route: Route) {
        this.route = route;
        this.arguments = {};
    }

    render(): TemplateResult {
        return this.route.render(this.arguments);
    }

    toString(): string {
        return `<RouteMatch url=${this.fullUrl} route=${this.route} arguments=${JSON.stringify(
            this.arguments,
        )}>`;
    }
}
