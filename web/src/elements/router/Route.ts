import "#elements/EmptyState";

import { assertDefaultExport, DefaultImportCallback, ImportCallback } from "#common/modules/types";

import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { html, nothing } from "lit";
import { until } from "lit/directives/until.js";

export const SLUG_REGEX = "[-a-zA-Z0-9_]+";
export const ID_REGEX = "\\d+";
export const UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";

export type RouteParameters = Record<string, string>;

export type RouteLoader = DefaultImportCallback<CustomElementConstructor>;

export type RouteHandler<P extends object = RouteParameters> = (
    parameters: P,
) => SlottedTemplateResult;

export interface RouteInit<P extends object = RouteParameters> {
    pattern: RegExp | string;
    loader?: RouteLoader | ImportCallback<object>;
    handler?: RouteHandler<P>;
}

export class Route {
    public readonly pattern: RegExp;

    #loader: RouteLoader | ImportCallback<object> | null;
    #handler: RouteHandler | null = null;

    constructor({ pattern, loader, handler }: RouteInit) {
        this.pattern = typeof pattern === "string" ? new RegExp(`^${pattern}$`) : pattern;

        this.#loader = loader || null;
        this.#handler = handler || null;
    }

    public redirect(to: string, raw = false): Route {
        this.#handler = async () => {
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

    public render(params: RouteParameters): SlottedTemplateResult {
        const invoke = (mod?: unknown) => {
            if (this.#handler) {
                return this.#handler(params);
            }

            if (!mod) {
                throw new TypeError(
                    "Route moduled did not provide a callback or load a module with a default export",
                );
            }

            assertDefaultExport<CustomElementConstructor>(mod);

            const tagName = window.customElements.getName(mod.default);

            if (!tagName) {
                throw new TypeError(
                    "Route provided a module that did not register a custom element",
                );
            }

            return StrictUnsafe(tagName, params);
        };

        if (this.#loader) {
            return until(
                this.#loader().then(invoke),
                html`<ak-empty-state loading></ak-empty-state>`,
            );
        }

        return invoke();
    }

    public toString(): string {
        return `<Route url=${this.pattern} callback=${this.#handler ? "true" : "false"}>`;
    }
}
