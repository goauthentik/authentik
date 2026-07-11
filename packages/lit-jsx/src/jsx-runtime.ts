import { createElementTemplate } from "./element.js";
import type * as JSXTypes from "./jsx.js";
import { mapJSXProps, type ReactiveElementConstructorLike } from "./properties.js";
import type { SlottedTemplateResult } from "./types.js";

export type CustomElementConstructor<T extends HTMLElement = HTMLElement> = new (
    ...args: never[]
) => T;

/**
 * A function component: props in, template out. `children` arrive inside the
 * props object (automatic-runtime shape), unlike the legacy two-argument
 * `LitFC` in `web/`, which continues to work as a plain function call.
 */
export type FC<P extends object = object> = (
    props: P & { children?: JSXTypes.JSXChildren },
) => SlottedTemplateResult | SlottedTemplateResult[];

export type ElementType = string | FC<never> | CustomElementConstructor;

function isCustomElementConstructor(type: object): type is CustomElementConstructor {
    return typeof type === "function" && "prototype" in type
        ? (type as { prototype: unknown }).prototype instanceof HTMLElement
        : false;
}

/**
 * Recursively drop child values JSX consumers expect to disappear
 * (`true`, `false`, `null`, `undefined`) — Lit would stringify booleans.
 */
function filterChildren(children: unknown): unknown {
    if (children === null || children === undefined || typeof children === "boolean") {
        return null;
    }

    if (Array.isArray(children)) {
        return children.map(filterChildren);
    }

    return children;
}

export function jsx(
    type: ElementType,
    props: Record<string, unknown>,
    _key?: PropertyKey,
): unknown {
    if (typeof type === "function") {
        if (isCustomElementConstructor(type)) {
            // `customElements.getName` expects the DOM lib's own
            // `CustomElementConstructor` (`new (...params: any[]) => HTMLElement`),
            // which doesn't structurally unify with this package's more permissive
            // `CustomElementConstructor` (a `never[]`-param constructor type, chosen
            // so any class — regardless of its own constructor signature — satisfies
            // it). The runtime value is unaffected; only the DOM lib type needs
            // satisfying here.
            const tagName = customElements.getName(
                type as unknown as Parameters<typeof customElements.getName>[0],
            );

            if (!tagName) {
                throw new TypeError(
                    `lit-jsx: custom element class "${type.name}" is not registered. ` +
                        `Import the module that defines it so its customElements.define ` +
                        `(or @customElement decorator) runs before rendering.`,
                );
            }

            return renderTag(tagName, props, type as ReactiveElementConstructorLike);
        }

        return (type as FC)(props);
    }

    return renderTag(type, props, customElements.get(type) as ReactiveElementConstructorLike);
}

function renderTag(
    tagName: string,
    props: Record<string, unknown>,
    ElementConstructor?: ReactiveElementConstructorLike,
): unknown {
    const mapped = mapJSXProps(props, ElementConstructor);
    mapped.children = filterChildren(mapped.children);
    return createElementTemplate(tagName, mapped);
}

export const jsxs = jsx;

/**
 * `<>…</>` — returns its (filtered) children; Lit renders arrays natively.
 */
export function Fragment(props: { children?: unknown }): unknown {
    return filterChildren(props.children);
}

/**
 * The JSX namespace TypeScript resolves for `jsxImportSource`.
 */
export namespace JSX {
    export type Element = SlottedTemplateResult | SlottedTemplateResult[];
    export type ElementType = import("./jsx-runtime.js").ElementType;

    // TypeScript's JSX class-component check requires `ElementClass` to be an
    // interface (not a type alias); it has no members of its own to add.
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    export interface ElementClass extends HTMLElement {}

    export interface ElementChildrenAttribute {
        children: object;
    }

    export interface IntrinsicAttributes {
        key?: PropertyKey;
    }

    export type IntrinsicElements = JSXTypes.IntrinsicElements;
}
