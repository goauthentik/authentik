import { AKElement } from "#elements/Base";
import {
    AKElementTagPrefix,
    CustomElementTagName,
    LitPropertyRecord,
    SlottedTemplateResult,
} from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { LitElement, nothing } from "lit";
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
export function StrictUnsafe(
    tagName: string,
    props?: LitPropertyRecord<LitElement>,
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

        for (const [key, value] of Object.entries(props || {})) {
            const propDeclaration = elementProperties.get(key);

            if (propDeclaration) {
                const prefix = propDeclaration.type === Boolean ? "?" : ".";
                filteredProps[`${prefix}${key}`] = value;

                continue;
            }

            if (observedAttributes.has(key) || key in ElementConstructor.prototype) {
                filteredProps[key] = String(value);

                continue;
            }

            throw new TypeError(
                `Property or attribute \`${key}\` is not defined on custom element ${tagName}`,
            );
        }

        return staticHTML`<${unsafeStatic(tagName)} ${spread(filteredProps)}></${unsafeStatic(tagName)}>`;
    });
}
