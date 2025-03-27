import DOMPurify from "dompurify";

import { render } from "@lit-labs/ssr";
import { collectResult } from "@lit-labs/ssr/lib/render-result.js";
import { TemplateResult, html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

export const DOM_PURIFY_STRICT: DOMPurify.Config = {
    ALLOWED_TAGS: ["#text"],
};

export async function renderStatic(input: TemplateResult): Promise<string> {
    return await collectResult(render(input));
}

/**
 * Purify a template result using DOMPurify.
 *
 * @param input Template result to purify
 */
export function purify(input: TemplateResult): TemplateResult {
    return html`${until(
        (async () => {
            const rendered = await renderStatic(input);
            const purified = DOMPurify.sanitize(rendered);
            return html`${unsafeHTML(purified)}`;
        })(),
    )}`;
}
