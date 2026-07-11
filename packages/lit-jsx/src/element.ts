import { isDirectiveResult, type MappedProps } from "./properties.js";
import { spread } from "./spread.js";

import { nothing, type TemplateResult } from "lit";
import { ref, type RefOrCallback } from "lit/directives/ref.js";
import { type StyleInfo, styleMap } from "lit/directives/style-map.js";
import { html as staticHTML, type StaticValue, unsafeStatic } from "lit/static-html.js";

/**
 * HTML elements that cannot have children or a closing tag.
 */
const VoidElementTagNames = new Set([
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]);

const staticTagCache = new Map<string, StaticValue>();

function staticTag(tagName: string): StaticValue {
    let tag = staticTagCache.get(tagName);

    if (!tag) {
        tag = unsafeStatic(tagName);
        staticTagCache.set(tagName, tag);
    }

    return tag;
}

function styleBinding(styleValue: unknown): unknown {
    if (styleValue === null || styleValue === undefined) {
        return nothing;
    }

    if (typeof styleValue === "string" || isDirectiveResult(styleValue)) {
        return styleValue;
    }

    return styleMap(styleValue as Readonly<StyleInfo>);
}

/**
 * Assemble a Lit template for a single element from mapped JSX props.
 *
 * `class`, `style`, and `ref` get dedicated template bindings so their
 * directives work; everything else flows through the spread directive.
 * Lit's static-html cache keys on the assembled strings, so each tag name
 * reuses one cached template shape.
 *
 * Expects `mapped.children` to already be filtered (booleans/nullish
 * dropped) — `jsx()` does this filtering before calling in here. Callers that
 * invoke this directly with, e.g., `children: false` for a void element will
 * throw, since only `undefined`/`null` are treated as "no children".
 */
export function createElementTemplate(tagName: string, mapped: MappedProps): TemplateResult {
    const tag = staticTag(tagName);
    const classBinding = mapped.classValue ?? nothing;
    const style = styleBinding(mapped.styleValue);
    const refDirective = ref(mapped.refValue as RefOrCallback | undefined);

    if (VoidElementTagNames.has(tagName)) {
        if (mapped.children !== undefined && mapped.children !== null) {
            throw new TypeError(
                `lit-jsx: <${tagName}> is a void element and cannot have children.`,
            );
        }

        return staticHTML`<${tag} class=${classBinding} style=${style} ${refDirective} ${spread(mapped.bindings)}>`;
    }

    return staticHTML`<${tag} class=${classBinding} style=${style} ${refDirective} ${spread(mapped.bindings)}>${mapped.children}</${tag}>`;
}
