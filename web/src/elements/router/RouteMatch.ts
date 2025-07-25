import { ROUTE_SEPARATOR } from "#common/constants";

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

export function getURLParam<T>(key: string, fallback: T): T {
    const params = getURLParams();
    if (key in params) {
        return params[key] as T;
    }
    return fallback;
}

export function getURLParams(): { [key: string]: unknown } {
    const params = {};
    if (window.location.hash.includes(ROUTE_SEPARATOR)) {
        const urlParts = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR, 2);
        const rawParams = decodeURIComponent(urlParts[1]);
        try {
            return JSON.parse(rawParams);
        } catch {
            return params;
        }
    }
    return params;
}

export function setURLParams(params: { [key: string]: unknown }, replace = true): void {
    const paramsString = JSON.stringify(params);
    const currentUrl = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR)[0];
    const newUrl = `#${currentUrl};${encodeURIComponent(paramsString)}`;
    if (replace) {
        history.replaceState(undefined, "", newUrl);
    } else {
        history.pushState(undefined, "", newUrl);
    }
}

export function updateURLParams(params: { [key: string]: unknown }, replace = true): void {
    const currentParams = getURLParams();
    for (const key in params) {
        currentParams[key] = params[key] as string;
    }
    setURLParams(currentParams, replace);
}
