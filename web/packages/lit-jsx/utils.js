import { spread } from "@open-wc/lit-helpers";

import { ifDefined } from "lit/directives/if-defined.js";
import { ref } from "lit/directives/ref.js";
import { html, unsafeStatic } from "lit/static-html.js";

/**
 *
 * @param {string} tagName
 * @param {Record<PropertyKey, unknown>} props
 * @returns
 */
export function parseProps(tagName, props) {
    /**
     * @type {Record<PropertyKey, unknown>}
     */
    const spreadable = {};
    const ElementConstructor = customElements.get(tagName);

    for (const [propName, value] of Object.entries(props)) {
        if (propName === "htmlFor") {
            spreadable.for = value;
            continue;
        }
        if (propName.startsWith("on")) {
            const eventName = propName.slice(2).toLowerCase();
            spreadable[`@${eventName}`] = value;
        } else if (typeof value === "boolean") {
            spreadable[`?${propName}`] = value;
        } else if (ElementConstructor) {
            spreadable[`.${propName}`] = value;
        } else {
            spreadable[`${propName}`] = value;
        }
    }

    console.log(spreadable);

    return spreadable;
}

/**
 *
 * @param {string} tagName
 * @param {*} props
 * @returns
 */
export function createElement(
    tagName,
    { className, children, ref: refProp, style = {}, ...props },
) {
    const tag = unsafeStatic(tagName);

    const result = html`
        <${tag} class="${ifDefined(className)}"
        ${ref(refProp)}
        ${spread(parseProps(tagName, props))}>
            ${children}
        </${tag}>
    `;

    return result;
}
