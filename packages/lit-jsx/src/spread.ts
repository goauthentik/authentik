/**
 * Adapted from: https://open-wc.org/blog/doing-a-flip-with-lit-html-2-0/
 *
 * `@open-wc/lit-helpers`'s `spread` directive only removes a binding when
 * `element[name] === prevData[key]` still holds for the *current* element
 * property value, which is never true for plain attributes (there is no such
 * JS property) or for values that already changed elsewhere. That leaves
 * stale attributes/properties/boolean-attributes behind across renders. This
 * fork tracks removals directly from the previous binding keys instead.
 *
 * This can be removed once Lit has an official spread directive:
 * https://github.com/lit/lit/pull/1960
 */

/**
 * @license
 * Original code by open-wc.org, licensed under the BSD-3-Clause license.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Copyright 2021 Open WC
 */

import { nothing } from "lit";
import { AsyncDirective, directive } from "lit/async-directive.js";
import type { ElementPart } from "lit/directive.js";

type EventListenerWithOptions = EventListenerOrEventListenerObject &
    Partial<AddEventListenerOptions>;

type SpreadData = Record<string, unknown>;

/**
 * A `directive` that applies a set of sigil-prefixed bindings to an element:
 * `"@click"` (event), `".selected"` (property), `"?disabled"` (boolean
 * attribute), and a bare name (standard attribute).
 */
class SpreadDirective extends AsyncDirective {
    host!: object;
    element!: Element;
    prevData: SpreadData = {};

    render(_spreadData: SpreadData): unknown {
        return nothing;
    }

    // Each update, apply the props and remove/clean up stale ones.
    update(part: ElementPart, [spreadData]: [SpreadData]): unknown {
        if (this.element !== part.element) {
            this.element = part.element;
        }

        this.host = part.options?.host || this.element;
        this.apply(spreadData);
        this.groom(spreadData);
        this.prevData = spreadData;

        return nothing;
    }

    // Apply props.
    apply(data: SpreadData): void {
        if (!data) return;

        const { prevData, element } = this;

        for (const key in data) {
            if (!Object.prototype.hasOwnProperty.call(data, key)) continue;

            const value = data[key];

            if (value === prevData[key]) {
                continue;
            }

            const name = key.slice(1);

            switch (key[0]) {
                case "@": {
                    // event listener
                    const prevHandler = prevData[key];

                    if (prevHandler) {
                        element.removeEventListener(
                            name,
                            this,
                            prevHandler as EventListenerWithOptions,
                        );
                    }

                    element.addEventListener(name, this, value as EventListenerWithOptions);
                    break;
                }
                case ".": // property
                    (element as unknown as SpreadData)[name] = value;
                    break;
                case "?": // boolean attribute
                    if (value) {
                        element.setAttribute(name, "");
                    } else {
                        element.removeAttribute(name);
                    }
                    break;
                default: // standard attribute
                    if (value !== null && value !== undefined) {
                        element.setAttribute(key, String(value));
                    } else {
                        element.removeAttribute(key);
                    }
                    break;
            }
        }
    }

    // Clean up any bindings that disappeared since the previous render.
    //
    // The upstream open-wc implementation guards removal with
    // `element[name] === prevData[key]`, which never holds for standard
    // attributes/properties (there is no such live JS property to compare
    // against), so removed bindings were silently left in place. This fork
    // removes a binding whenever its key is absent (or nullish) in the new
    // data, regardless of the element's current live value.
    groom(data: SpreadData): void {
        const { prevData, element } = this;

        if (!prevData) return;

        for (const key in prevData) {
            if (!Object.prototype.hasOwnProperty.call(prevData, key)) continue;

            const removed =
                !data || !(key in data) || data[key] === undefined || data[key] === null;

            if (!removed) continue;

            const name = key.slice(1);

            switch (key[0]) {
                case "@": {
                    // event listener
                    const value = prevData[key];
                    element.removeEventListener(name, this, value as EventListenerWithOptions);
                    break;
                }
                case ".": // property
                    (element as unknown as SpreadData)[name] = undefined;
                    break;
                case "?": // boolean attribute
                    element.removeAttribute(name);
                    break;
                default: // standard attribute
                    element.removeAttribute(key);
                    break;
            }
        }
    }

    handleEvent(event: Event): void {
        const value = this.prevData[`@${event.type}`];

        if (typeof value === "function") {
            (value as (event: Event) => void).call(this.host, event);
        } else {
            (value as EventListenerObject).handleEvent(event);
        }
    }

    disconnected(): void {
        const { prevData, element } = this;

        for (const key in prevData) {
            if (key[0] !== "@") continue;
            // event listener
            const value = prevData[key];
            element.removeEventListener(key.slice(1), this, value as EventListenerWithOptions);
        }
    }

    reconnected(): void {
        const { prevData, element } = this;

        for (const key in prevData) {
            if (key[0] !== "@") continue;
            // event listener
            const value = prevData[key];
            element.addEventListener(key.slice(1), this, value as EventListenerWithOptions);
        }
    }
}

export const spread = directive(SpreadDirective);
