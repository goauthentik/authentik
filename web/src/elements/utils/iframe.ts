/**
 * @file IFrame Utilities
 */

import { renderStaticHTMLUnsafe } from "#common/purify";

import { MaybeCompiledTemplateResult } from "lit";

export interface CreateHTMLObjectInit {
    body: string | MaybeCompiledTemplateResult;
    head?: string | MaybeCompiledTemplateResult;
}

/**
 * Render untrusted HTML to a string without escaping it.
 *
 * @returns {string} The rendered HTML string.
 */
export function createDocumentTemplate(init: CreateHTMLObjectInit): string {
    const body = renderStaticHTMLUnsafe(init.body);
    const head = init.head ? renderStaticHTMLUnsafe(init.head) : "";

    return `<!DOCTYPE html>
        <html>
            <head>
                ${head}
            </head>
            <body>
                ${body}
            </body>
        </html>`;
}
