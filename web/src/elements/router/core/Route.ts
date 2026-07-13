/**
 * @file Route definition for path-based routing.
 *
 * A `Route` wraps a `URLPattern` constructed **once** at construction (never
 * per match) and renders a template for the matched path parameters. The
 * `name` is a stable identifier used for Sentry span naming and href
 * generation.
 */

import { type RouteParameterRecord } from "#elements/router/core/parameters";
import { type SlottedTemplateResult } from "#elements/types";

import { html, nothing, TemplateResult } from "lit";
import { until } from "lit/directives/until.js";

export type RouteRenderCallback<P> = (
    params: P,
) => SlottedTemplateResult | Promise<SlottedTemplateResult>;

export class Route<P extends RouteParameterRecord = RouteParameterRecord> {
    /**
     * The compiled pattern, built once at construction.
     */
    public readonly pattern: URLPattern;

    /**
     * Stable identifier for Sentry spans and href generation.
     */
    public readonly name: string;

    #render: RouteRenderCallback<P>;

    constructor(
        patternInit: URLPatternInit | string,
        render: RouteRenderCallback<P>,
        name?: string,
    ) {
        const init: URLPatternInit =
            typeof patternInit === "string" ? { pathname: patternInit } : patternInit;

        this.pattern = new URLPattern(init);
        this.name = name ?? init.pathname ?? "";
        this.#render = render;
    }

    /**
     * Render the route's template for the given path parameters.
     *
     * The pending state is `nothing`; loading UI is the outlet's concern.
     */
    render(params: P): TemplateResult {
        return html`${until(this.#render(params), nothing)}`;
    }
}
