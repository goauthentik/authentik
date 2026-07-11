import { nothing, type PropertyDeclaration } from "lit";

import { normalizeClassValue, type ClassValue } from "./class-names.js";
import { resolveEventName } from "./events.js";

export const Prefix = {
    Property: ".",
    BooleanAttribute: "?",
    Attribute: "",
    Event: "@",
} as const;

export type Prefix = (typeof Prefix)[keyof typeof Prefix];

type WrappedPropertyDeclaration = PropertyDeclaration<unknown, unknown> & { wrapped?: boolean };

/**
 * Given a Lit property declaration, determine the sigil for rendering the
 * property as a property, attribute, or boolean attribute.
 *
 * Ported from `web/src/elements/utils/unsafe.ts`, with one correction: Lit's
 * `elementProperties` map stores each declaration exactly as authored, so an
 * omitted `attribute` key is `undefined`, not the normalized default of
 * `true`. Only an *explicit* `attribute: false` should fall back to a
 * property binding; `unsafe.ts`'s `!declaration.attribute` check treats the
 * common no-`attribute`-key case (e.g. `{ type: String }`) the same as
 * `attribute: false`, which misses reactive properties declared without
 * spelling out `attribute: true`.
 */
export function resolvePrefix(declaration: WrappedPropertyDeclaration): Prefix {
    if (declaration.attribute === false) {
        return Prefix.Property;
    }

    if ("wrapped" in declaration && declaration.wrapped && !declaration.type) {
        return Prefix.Attribute;
    }

    switch (declaration.type) {
        case String:
            return Prefix.Attribute;
        case Boolean:
            return Prefix.BooleanAttribute;
        default:
            return Prefix.Property;
    }
}

/**
 * Determine the bound name for a declared property, honoring custom attribute
 * names such as `@property({ attribute: "data-level" })`.
 *
 * Ported from `web/src/elements/utils/unsafe.ts`.
 */
export function resolvePropertyName(
    declaration: WrappedPropertyDeclaration,
    prefix: Prefix,
    key: string,
): string {
    if (prefix === Prefix.Property) {
        return key;
    }

    if (typeof declaration.attribute === "string") {
        return declaration.attribute;
    }

    return key;
}

/**
 * Detect a Lit `DirectiveResult` without importing the directive machinery.
 */
export function isDirectiveResult(value: unknown): boolean {
    return typeof value === "object" && value !== null && "_$litDirective$" in value;
}

/**
 * The subset of a `ReactiveElement` constructor that prop mapping reads.
 * Structural so unit tests can pass plain objects.
 */
export interface ReactiveElementConstructorLike {
    elementProperties?: Map<PropertyKey, PropertyDeclaration>;
    observedAttributes?: readonly string[];
    prototype: object;
}

export interface MappedProps {
    /**
     * Sigil-prefixed bindings for the spread directive:
     * `"@click"`, `".selected"`, `"?disabled"`, `"for"`.
     */
    bindings: Record<string, unknown>;
    classValue?: unknown;
    styleValue?: unknown;
    refValue?: unknown;
    children?: unknown;
}

/**
 * Native element properties that must be set as properties, not attributes,
 * to behave correctly after user interaction (the attribute only sets the
 * default state).
 */
const NativePropertyNames = new Set(["value", "checked", "selected"]);

/**
 * Map JSX props to Lit bindings.
 *
 * Declared reactive properties resolve through the constructor's
 * `elementProperties` metadata; everything else falls back to deterministic
 * heuristics documented in the package README.
 */
export function mapJSXProps(
    props: Record<string, unknown>,
    ElementConstructor?: ReactiveElementConstructorLike,
): MappedProps {
    const bindings: Record<string, unknown> = {};
    const mapped: MappedProps = { bindings };

    const elementProperties = ElementConstructor?.elementProperties;

    for (const [name, rawValue] of Object.entries(props)) {
        // `nothing` is a template-part sentinel; the spread directive would
        // stringify it. `undefined` gets the intended remove/skip behavior.
        const value = rawValue === nothing ? undefined : rawValue;

        switch (name) {
            case "children":
                mapped.children = value;
                continue;
            case "key":
                continue;
            case "ref":
                mapped.refValue = value;
                continue;
            case "class":
            case "className": {
                if (isDirectiveResult(value)) {
                    mapped.classValue = value;
                } else {
                    const normalized = normalizeClassValue(value as ClassValue);
                    mapped.classValue = normalized === "" ? undefined : normalized;
                }
                continue;
            }
            case "style":
                mapped.styleValue = value;
                continue;
            case "htmlFor":
                bindings.for = value;
                continue;
        }

        const eventName = resolveEventName(name);

        if (eventName) {
            bindings[`${Prefix.Event}${eventName}`] = value;
            continue;
        }

        const declaration = elementProperties?.get(name);

        if (declaration) {
            const prefix = resolvePrefix(declaration);
            bindings[`${prefix}${resolvePropertyName(declaration, prefix, name)}`] = value;
            continue;
        }

        if (NativePropertyNames.has(name)) {
            bindings[`${Prefix.Property}${name}`] = value;
            continue;
        }

        if (typeof value === "boolean") {
            bindings[`${Prefix.BooleanAttribute}${name}`] = value;
            continue;
        }

        if (
            typeof value === "function" ||
            (typeof value === "object" && value !== null && !isDirectiveResult(value))
        ) {
            bindings[`${Prefix.Property}${name}`] = value;
            continue;
        }

        bindings[name] = value;
    }

    return mapped;
}
