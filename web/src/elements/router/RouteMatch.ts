import { Route } from "#elements/router/Route";

import { TemplateResult } from "lit";

export class RouteMatch {
    route: Route;
    arguments: { [key: string]: string };
    fullURL: string;

    constructor(route: Route, fullUrl: string) {
        this.route = route;
        this.arguments = {};
        this.fullURL = fullUrl;
    }

    render(): TemplateResult {
        return this.route.render(this.arguments);
    }

    /**
     * Convert the matched Route's URL regex to a sanitized, readable URL by replacing
     * all regex values with placeholders according to the name of their regex group.
     *
     * @returns The sanitized URL for logging/tracing.
     */
    sanitizedURL() {
        let cleanedURL = this.fullURL;
        for (const match of Object.keys(this.arguments)) {
            const value = this.arguments[match];
            cleanedURL = cleanedURL?.replace(value, `:${match}`);
        }
        return cleanedURL;
    }

    toString(): string {
        return `<RouteMatch url=${this.sanitizedURL()} route=${this.route} arguments=${JSON.stringify(
            this.arguments,
        )}>`;
    }
}
