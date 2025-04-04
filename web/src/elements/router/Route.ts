import "@goauthentik/elements/EmptyState";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { TemplateResult, html, nothing } from "lit";
import { until } from "lit/directives/until.js";

export type PrimitiveRouteParameter = string | number | boolean | null | undefined;
export type RouteParameterRecord = { [key: string]: PrimitiveRouteParameter };

export type RouteCallback<P = unknown> = (
    params: P,
) => SlottedTemplateResult | Promise<SlottedTemplateResult>;

export type RouteInitTuple = [string | RegExp, RouteCallback | undefined];

export class Route<P = unknown> {
    public readonly pattern: URLPattern;

    #callback: RouteCallback<P>;

    constructor(patternInit: URLPatternInit | string, callback: RouteCallback<P>) {
        this.pattern = new URLPattern(
            typeof patternInit === "string"
                ? {
                      pathname: patternInit,
                  }
                : patternInit,
        );

        this.#callback = callback;
    }

    /**
     * Create a new redirect route.
     *
     * @param patternInit The pattern to match.
     * @param to The URL to redirect to.
     * @param raw Whether to use the raw URL or not.
     */
    static redirect(patternInit: URLPatternInit | string, to: string, raw = false): Route<unknown> {
        return new Route(patternInit, () => {
            console.debug(`authentik/router: redirecting ${to}`);

            if (!raw) {
                window.location.hash = `#${to}`;
            } else {
                window.location.hash = to;
            }

            return nothing;
        });
    }

    render(params: P): TemplateResult {
        return html`${until(
            this.#callback(params),
            html`<ak-empty-state ?loading=${true}></ak-empty-state>`,
        )}`;
    }
}
