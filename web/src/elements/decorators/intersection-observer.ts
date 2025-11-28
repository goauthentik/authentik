/**
 * @file Intersection Observer Decorator for LitElement
 */

import { LitElement } from "lit";
import { property } from "lit/decorators.js";

/**
 * Type for the decorator
 */
export type IntersectionDecorator = <T extends LitElement>(target: T, propertyKey: keyof T) => void;

/**
 * A decorator that applies an IntersectionObserver to the element.
 * This is useful for lazy-loading elements that are not visible on the screen.
 *
 * @param init Configuration options for the IntersectionObserver
 *
 * ```ts
 * class MyElement extends LitElement {
 *     \@intersectionObserver()
 *     protected visible!: boolean;
 *
 *     \@intersectionObserver({ threshold: 0.5, rootMargin: '50px' })
 *     protected halfVisible!: boolean;
 *
 *     render() {
 *         if (!this.visible) return nothing;
 *
 *         return html`
 *             <div>
 *                 Content is visible!
 *                 ${this.halfVisible ? html`<p>More than 50% visible</p>` : ''}
 *             </div>
 *         `;
 *     }
 * }
 * ```
 */
export function intersectionObserver(init: IntersectionObserverInit = {}): IntersectionDecorator {
    return <T extends LitElement, K extends keyof T>(target: T, key: K) => {
        //#region Prepare observer

        property({ attribute: false, useDefault: false })(target, key);

        const observerCallback: IntersectionObserverCallback = (entries) => {
            for (const entry of entries) {
                const currentTarget = entry.target as T;
                const cachedIntersecting = currentTarget[key];

                if (cachedIntersecting !== entry.isIntersecting) {
                    Object.assign(currentTarget, {
                        [key]: entry.isIntersecting,
                    });

                    currentTarget.requestUpdate(key, cachedIntersecting);
                }
            }
        };

        //#endregion

        //#region Lifecycle

        const observer = new IntersectionObserver(observerCallback, {
            root: null,
            rootMargin: "0px",
            threshold: 0,
            ...init,
        });

        const { connectedCallback, disconnectedCallback } = target;

        target.connectedCallback = function (this: T) {
            connectedCallback?.call(this);

            if (this.hasUpdated) {
                observer.observe(this);
            } else {
                this.updateComplete.then(() => {
                    observer.observe(this);
                });
            }
        };

        target.disconnectedCallback = function (this: LitElement) {
            disconnectedCallback?.call(this);

            if (observer) {
                observer.disconnect();
            }
        };
        //#endregion
    };
}
