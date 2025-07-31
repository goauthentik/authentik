import { createElement } from "./utils.js";

/**
 * @param {unknown} elementLike
 * @returns {elementLike is LitJSX.CustomElementConstructor}
 */
function isCustomElementConstructor(elementLike) {
    return typeof elementLike === "function" && elementLike.prototype instanceof HTMLElement;
}

/**
 *
 * @param {LitJSX.ElementType | LitJSX.CustomElementComponent} elementLike
 * @param {unknown} props
 */
export function jsx(elementLike, props) {
    console.log({ elementLike, props });
    if (typeof elementLike === "function") {
        if (isCustomElementConstructor(elementLike)) {
            const tagName = customElements.getName(elementLike);

            if (!tagName) {
                throw new Error(`Custom element ${elementLike.name} is not registered`);
            }

            // Render the custom web component as any other html element.
            return createElement(tagName, props);
        }

        // @ts-ignore
        return elementLike(props);
    }

    // @ts-ignore
    return createElement(elementLike, props);
}

export { jsx as jsxs };

/**
 *
 * @param {LitJSX.Fragment} fragment
 * @returns {LitJSX.ElementType[]}
 */
export function Fragment(fragment) {
    return Array.isArray(fragment.children) ? fragment.children : [fragment.children];
}
