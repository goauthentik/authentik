import DOMPurify from "dompurify";

import { render } from "@lit-labs/ssr";
import { collectResult } from "@lit-labs/ssr/lib/render-result.js";
import { TemplateResult, html } from "lit";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

export function purify(input: TemplateResult): TemplateResult {
    return html`${until(
        (async () => {
            const rendered = await collectResult(render(input));
            const purified = DOMPurify.sanitize(rendered);
            return html`${unsafeHTML(purified)}`;
        })(),
    )}`;
}
