import "@goauthentik/elements/EmptyState";

import { msg } from "@lit/localize";
import { html } from "lit";
import type { TemplateResult } from "lit";

export const customEvent = (name: string, details = {}) =>
    new CustomEvent(name as string, {
        composed: true,
        bubbles: true,
        detail: details,
    });

// "Unknown" seems to violate some obscure Typescript rule and doesn't work here, although it
// should.
//
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isCustomEvent = (v: any): v is CustomEvent =>
    v instanceof CustomEvent && "detail" in v;

export const loading = <T>(v: T, actual: TemplateResult) =>
    v
        ? actual
        : html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}> </ak-empty-state>`;
