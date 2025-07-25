import "#elements/EmptyState";

import { SlottedTemplateResult } from "#elements/types";

import { html, nothing, TemplateResult } from "lit";
import { until } from "lit/directives/until.js";

export const SLUG_REGEX = "[-a-zA-Z0-9_]+";
export const ID_REGEX = "\\d+";
export const UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";

export type URLParameterRecord = Record<string, string>;

export type RouteCallback<P extends URLParameterRecord> = (
    args: P,
) => Promise<SlottedTemplateResult>;

export class Route<P extends URLParameterRecord = URLParameterRecord> {
    public readonly url: RegExp;

    private element?: TemplateResult;
    #callback?: RouteCallback<P>;

    constructor(url: RegExp, callback?: RouteCallback<P>) {
        this.url = url;
        this.#callback = callback;
    }

    redirect(to: string, raw = false): Route<P> {
        this.#callback = async () => {
            console.debug(`authentik/router: redirecting ${to}`);
            if (!raw) {
                window.location.hash = `#${to}`;
            } else {
                window.location.hash = to;
            }

            return nothing;
        };
        return this;
    }

    then(render: (args: P) => TemplateResult): Route<P> {
        this.#callback = async (args) => {
            return render(args);
        };
        return this;
    }

    thenAsync(render: (args: P) => Promise<TemplateResult>): Route<P> {
        this.#callback = render;
        return this;
    }

    render(args: P): TemplateResult {
        if (this.#callback) {
            return html`${until(
                this.#callback(args),
                html`<ak-empty-state loading></ak-empty-state>`,
            )}`;
        }
        if (this.element) {
            return this.element;
        }
        throw new Error("Route does not have callback or element");
    }

    toString(): string {
        return `<Route url=${this.url} callback=${this.#callback ? "true" : "false"}>`;
    }
}
