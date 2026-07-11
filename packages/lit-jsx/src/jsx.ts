import type { ClassValue } from "./class-names.js";
import type { DOMEventHandlerNames } from "./events.js";
import type { OwnPropertyRecord, SlottedTemplateResult } from "./types.js";

import type { LitElement, nothing } from "lit";
import type { DirectiveResult } from "lit/directive.js";
import type { RefOrCallback } from "lit/directives/ref.js";
import type { StyleInfo } from "lit/directives/style-map.js";

/**
 * lit-html's public `DirectiveResult<C>` is (deliberately) an empty
 * interface — its `_$litDirective$` brand is an implementation detail not
 * present in the published type. That makes it structurally equivalent to
 * `{}`, which absorbs every non-nullish value: `number | DirectiveResult`
 * would silently accept a `string`. Intersecting with `object` restores the
 * exclusion of primitives (unlike `{}`, `object` does not admit them), so a
 * union with `Directive` only accepts real (object-shaped) directive
 * results.
 */
type Directive = DirectiveResult & object;

/**
 * Anything renderable in child position: template results, primitives,
 * booleans/nullish (dropped by the runtime), and nested arrays of the same.
 */
export type JSXChild = SlottedTemplateResult | number | boolean | undefined;
export type JSXChildren = JSXChild | readonly JSXChildren[];

export type AttributeValue =
    | string
    | number
    | boolean
    | null
    | undefined
    | typeof nothing
    | Directive;

export type DataAttributes = Record<`data-${string}`, AttributeValue>;
export type AriaAttributes = Record<
    `aria-${string}`,
    string | undefined | typeof nothing | Directive
>;

/**
 * Props shared by every element, intrinsic or custom.
 */
export interface JSXBaseProps<E extends HTMLElement = HTMLElement> {
    key?: PropertyKey;
    ref?: RefOrCallback<E>;
    class?: ClassValue | Directive;
    className?: ClassValue | Directive;
    style?: string | Readonly<StyleInfo> | Directive;
    children?: JSXChildren;
    autofocus?: boolean;
    dir?: string;
    hidden?: boolean;
    id?: string;
    lang?: string;
    part?: string;
    role?: string;
    slot?: string;
    tabindex?: number | string;
    title?: string;
}

/**
 * Typed handlers for standard DOM events, derived from the canonical
 * runtime map so names and events can never drift apart.
 */
export type DOMEventHandlers = {
    [K in keyof typeof DOMEventHandlerNames]?: (
        event: GlobalEventHandlersEventMap[(typeof DOMEventHandlerNames)[K]],
    ) => void;
};

/**
 * Permissive handlers for custom events (`onAkChange` and friends).
 * Only custom elements get these; intrinsics stay strict.
 */
export type CustomEventHandlers = Record<`on${string}`, ((event: Event) => void) | undefined>;

/**
 * The element-specific props of an intrinsic element: own writable
 * primitive properties (value/checked/width/…), each also accepting a
 * directive result.
 */
export type IntrinsicPrimitiveProps<E extends HTMLElement> = {
    [K in keyof OwnPropertyRecord<E, HTMLElement> as OwnPropertyRecord<E, HTMLElement>[K] extends
        | string
        | number
        | boolean
        ? K
        : never]?: OwnPropertyRecord<E, HTMLElement>[K] | Directive;
};

export type IntrinsicElementProps<E extends HTMLElement> = JSXBaseProps<E> &
    DOMEventHandlers &
    DataAttributes &
    AriaAttributes &
    IntrinsicPrimitiveProps<E>;

/**
 * Props for a Lit-based custom element: its own writable properties
 * (beyond LitElement), plus custom event handlers.
 */
export type CustomElementProps<E extends HTMLElement> = JSXBaseProps<E> &
    DOMEventHandlers &
    CustomEventHandlers &
    DataAttributes &
    AriaAttributes &
    Partial<OwnPropertyRecord<E, LitElement>>;

export type IntrinsicElements = {
    [K in keyof HTMLElementTagNameMap]: HTMLElementTagNameMap[K] extends LitElement
        ? CustomElementProps<HTMLElementTagNameMap[K]>
        : IntrinsicElementProps<HTMLElementTagNameMap[K]>;
};
