import type { Config as DOMPurifyConfig } from "dompurify";
import DOMPurify from "dompurify";

import { render } from "@lit-labs/ssr";
import { collectResult } from "@lit-labs/ssr/lib/render-result.js";
import { TemplateResult, html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

export const DOM_PURIFY_STRICT = {
    ALLOWED_TAGS: ["#text"],
} as const satisfies DOMPurifyConfig;

export async function renderStatic(input: TemplateResult): Promise<string> {
    return await collectResult(render(input));
}

export function purify(input: TemplateResult): TemplateResult {
    return html`${until(
        (async () => {
            const rendered = await renderStatic(input);
            const purified = DOMPurify.sanitize(rendered);
            return html`${unsafeHTML(purified)}`;
        })(),
    )}`;
}
