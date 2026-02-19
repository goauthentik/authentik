import { AKElement } from "#elements/Base";
import {
    AKElementTagPrefix,
    CustomElementTagName,
    LitPropertyRecord,
    SlottedTemplateResult,
} from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { LitElement, nothing, PropertyDeclaration } from "lit";
import { html as staticHTML, unsafeStatic } from "lit-html/static.js";
import { guard } from "lit/directives/guard.js";

/**
 * Asserts that a custom element with the given tag name is registered.
 */
export function assertAKRegisteredElement(
    tagName: string,
): asserts tagName is CustomElementTagName {
    if (!customElements.get(tagName)) {
        throw new TypeError(`Custom element ${tagName} is not defined`);
    }

    if (!tagName.startsWith(AKElementTagPrefix)) {
        throw new TypeError(`Custom element ${tagName} is not an Authentik element`);
    }
}

/**
 * Type predicate to determine if a given {@linkcode CustomElementConstructor}
 * extends {@linkcode AKElement}.
 */
export function isAKElementConstructor(input: CustomElementConstructor): input is typeof AKElement {
    return Object.prototype.isPrototypeOf.call(AKElement, input);
}

export const Prefix = {
    Property: ".",
    BooleanAttribute: "?",
    Attribute: "",
} as const;

export type Prefix = (typeof Prefix)[keyof typeof Prefix];

/**
 * Given a Lit property declaration, determine the appropriate prefix for rendering the property as either a property or an attribute, based on the declaration's type and attribute configuration.
 *
 * @param propDeclaration The Lit property declaration to analyze.
 * @returns The determined prefix for rendering the property.
 */
function resolvePrefix<T extends PropertyDeclaration<unknown, unknown>>(
    propDeclaration: T,
): Prefix {
    if (!propDeclaration.attribute) {
        return Prefix.Property;
    }

    switch (propDeclaration.type) {
        case String:
            return Prefix.Attribute;
        case Boolean:
            return Prefix.BooleanAttribute;
        default:
            return Prefix.Property;
    }
}

/**
 * Given a Lit property declaration, a resolved prefix, and the original property key,
 * determine the appropriate name to use for rendering the property,
 * taking into account any custom attribute name specified in the declaration.
 */
function resolvePropertyName<T extends PropertyDeclaration<unknown, unknown>>(
    propDeclaration: T,
    prefix: Prefix,
    key: string,
): string {
    if (prefix === Prefix.Property) {
        return key;
    }

    if ("attribute" in propDeclaration && typeof propDeclaration.attribute === "string") {
        return propDeclaration.attribute;
    }

    return key;
}
/**
 * Given a pre-registered custom element tag name and a record of properties,
 * render the element with the given properties applied.
 *
 * @param tagName The custom element tag name.
 * @param props A record of properties to apply to the element.
 *
 * @returns A {@linkcode SlottedTemplateResult} rendering the custom element.
 */
export function StrictUnsafe<T extends CustomElementTagName>(
    tagName: T,
    props?: LitPropertyRecord<HTMLElementTagNameMap[T]>,
): SlottedTemplateResult;

export function StrictUnsafe<T extends AKElement>(
    tagName: string,
    props?: LitPropertyRecord<T>,
): SlottedTemplateResult;

export function StrictUnsafe<T extends string>(
    tagName: string,
    props?: T extends CustomElementTagName
        ? LitPropertyRecord<HTMLElementTagNameMap[T]>
        : LitPropertyRecord<LitElement>,
): SlottedTemplateResult;

export function StrictUnsafe<T extends string>(
    tagName: string,
    props?: T extends CustomElementTagName
        ? LitPropertyRecord<HTMLElementTagNameMap[T]>
        : LitPropertyRecord<LitElement>,
): SlottedTemplateResult {
    return guard([tagName, props], () => {
        if (!tagName) {
            return nothing;
        }

        if (!tagName.startsWith(AKElementTagPrefix)) {
            throw new TypeError(`Custom element ${tagName} is not an authentik element`);
        }

        const ElementConstructor = customElements.get(tagName);

        if (!ElementConstructor) {
            throw new TypeError(`Custom element ${tagName} is not defined`);
        }

        if (!isAKElementConstructor(ElementConstructor)) {
            throw new TypeError(`Custom element ${tagName} is not an authentik element`);
        }

        const { elementProperties } = ElementConstructor;
        const observedAttributes = new Set(ElementConstructor.observedAttributes);

        const filteredProps: Record<string, unknown> = {};

        for (const [propName, propValue] of Object.entries(props || {})) {
            const propDeclaration = elementProperties.get(propName);

            if (propDeclaration) {
                const prefix = resolvePrefix(propDeclaration);
                const name = resolvePropertyName(propDeclaration, prefix, propName);

                filteredProps[`${prefix}${name}`] = propValue;

                continue;
            }

            if (observedAttributes.has(propName) || propName in ElementConstructor.prototype) {
                filteredProps[propName] = String(propValue);
            }
        }

        return staticHTML`<${unsafeStatic(tagName)} ${spread(filteredProps)}></${unsafeStatic(tagName)}>`;
    });
}
