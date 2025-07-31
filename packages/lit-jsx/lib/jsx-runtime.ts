import { isCustomElementConstructor, isElementFactory } from "./predicates.js";
import { ComponentProps, createElement } from "./utils.js";

import type * as Lit from "@goauthentik/lit-jsx/types/lit-jsx.d.ts";

/**
 * JSX factory for Lit elements.
 */
export function jsx(
    elementLike: Lit.ElementType | Lit.ElementFactoryLike,
    props: ComponentProps,
): Lit.LitNode {
    console.log({ elementLike, props });
    if (isElementFactory(elementLike)) {
        if (isCustomElementConstructor(elementLike)) {
            const tagName = customElements.getName(elementLike);

            if (!tagName) {
                throw new Error(`Custom element ${elementLike.name} is not registered`);
            }

            // Render the custom web component as any other html element.
            return createElement(tagName, props);
        }

        return elementLike(props);
    }

    return createElement(elementLike, props);
}

export { jsx as jsxAttr, jsx as jsxDEV, jsx as jsxEscape, jsx as jsxs, jsx as jsxTemplate };

/**
 * HTML Fragment factory for Lit elements.
 */
export function Fragment(fragment: Lit.Fragment): Lit.ElementType[] {
    return Array.isArray(fragment.children) ? fragment.children : [fragment.children];
}
