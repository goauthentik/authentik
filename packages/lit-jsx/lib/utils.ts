import { spread } from "@open-wc/lit-helpers";

import { ifDefined } from "lit/directives/if-defined.js";
import { ref, RefOrCallback } from "lit/directives/ref.js";
import { styleMap } from "lit/directives/style-map.js";
import { html, unsafeStatic } from "lit/static-html.js";

export type CSSProperties = Record<string, string | number>;

/**
 *
 */
export function parseProps(tagName: string, props: Record<PropertyKey, unknown>) {
    const spreadable: Record<PropertyKey, unknown> = {};

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

export interface ComponentProps {
    className?: string;
    children?: unknown;
    ref?: RefOrCallback;
    style?: CSSProperties;
    [key: PropertyKey]: unknown;
}

/**
 *
 * @returns
 */
export function createElement<P = unknown>(
    tagName: string,
    { className, children, ref: refProp, style, ...props }: ComponentProps & P,
) {
    const tag = unsafeStatic(tagName);

    const result = html`
        <${tag} class=${ifDefined(className)}
        ${ref(refProp)}
        ${spread(parseProps(tagName, props))}
        style=${ifDefined(style ? styleMap(style) : null)}
        >
            ${children}
        </${tag}>
    `;

    return result;
}
