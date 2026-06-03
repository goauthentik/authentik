import { ROUTE_SEPARATOR } from "#common/constants";

import { Route } from "#elements/router/Route";
import { RouteParameterRecord } from "#elements/router/shared";

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

export function getURLParams(): RouteParameterRecord {
    const params = {};
    if (window.location.hash.includes(ROUTE_SEPARATOR)) {
        const urlParts = window.location.hash.slice(1).split(ROUTE_SEPARATOR, 2);
        const rawParams = decodeURIComponent(urlParts[1]);
        try {
            return JSON.parse(rawParams);
        } catch {
            return params;
        }
    }
    return params;
}

export function getURLParam<T>(key: string, fallback: T): T {
    const params = getURLParams();
    if (key in params) {
        return params[key] as T;
    }
    return fallback;
}

/**
 * Serialize route parameters to a JSON string, removing empty values.
 *
 * @param params The route parameters to serialize.
 */
export function prepareURLParams(params: RouteParameterRecord): RouteParameterRecord {
    const preparedParams: RouteParameterRecord = {};
    for (const [key, value] of Object.entries(params)) {
        if (value !== null && value !== undefined && value !== "") {
            preparedParams[key] = value;
        }
    }
    return preparedParams;
}

export function serializeURLParams(params: RouteParameterRecord): string {
    const preparedParams = prepareURLParams(params);

    return Object.keys(preparedParams).length === 0 ? "" : JSON.stringify(preparedParams);
}

export function setURLParams(params: RouteParameterRecord, replace = true): void {
    const [currentHash] = window.location.hash.slice(1).split(ROUTE_SEPARATOR);
    let nextHash = "#" + currentHash;
    const preparedParams = prepareURLParams(params);

    if (Object.keys(preparedParams).length) {
        nextHash += ROUTE_SEPARATOR + encodeURIComponent(JSON.stringify(preparedParams));
    }

    if (replace) {
        history.replaceState(undefined, "", nextHash);
    } else {
        history.pushState(undefined, "", nextHash);
    }
}

export function updateURLParams(params: RouteParameterRecord, replace = true): void {
    setURLParams({ ...getURLParams(), ...params }, replace);
}
