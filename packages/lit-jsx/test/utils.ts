import type * as Lit from "@goauthentik/lit-jsx/types/lit-jsx.d.ts";

import createDOMPurify, { Config as DOMPurifyConfig, WindowLike } from "dompurify";
import { JSDOM } from "jsdom";
import { format } from "prettier";

import { render, ServerRenderedTemplate } from "@lit-labs/ssr";
import { collectResult } from "@lit-labs/ssr/lib/render-result.js";

export class Purifier {
    #window = new JSDOM("").window;
    #DOMPurify = createDOMPurify(this.#window as WindowLike);

    public sanitize(html: string, config?: DOMPurifyConfig) {
        return this.#DOMPurify.sanitize(html, config);
    }
}

const purifier = new Purifier();

export async function renderStaticLit(value: unknown) {
    const result = await collectResult(render(value));

    const sanitized = purifier.sanitize(result);
    const formatted = await format(sanitized, {
        parser: "html",
    });

    return formatted.trim();
}

export function renderVariants(
    ...inputs: Array<ServerRenderedTemplate | Lit.LitNode>
): Promise<string[]> {
    return Promise.all(inputs.map((input) => renderStaticLit(input)));
}
