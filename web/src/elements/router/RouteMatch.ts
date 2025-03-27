import { ROUTE_SEPARATOR } from "@goauthentik/common/constants";
import { Route } from "@goauthentik/elements/router/Route";

import { TemplateResult } from "lit";

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

export function getURLParams(): { [key: string]: unknown } {
    const params = {};

    if (!window.location.hash.includes(ROUTE_SEPARATOR)) return params;

    const urlParts = window.location.hash.slice(1, Infinity).split(ROUTE_SEPARATOR, 2);
    const rawParams = decodeURIComponent(urlParts[1]);

    try {
        return JSON.parse(rawParams);
    } catch {
        return params;
    }
}

export function getURLParam<T>(key: string, fallback: T): T {
    const params = getURLParams();

    if (Object.hasOwn(params, key)) {
        return params[key] as T;
    }

    return fallback;
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

    for (const [key, value] of Object.entries(params)) {
        currentParams[key] = value;
    }

    setURLParams(currentParams, replace);
}
