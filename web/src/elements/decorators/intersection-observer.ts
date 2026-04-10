/**
 * @file Intersection Observer Decorator for LitElement
 */

import { findNearestBoxTarget, isInViewport } from "#elements/utils/viewport";

import { LitElement, PropertyValues } from "lit";
import { property } from "lit/decorators.js";

/**
 * Type for the decorator
 */
export type IntersectionDecorator = <T extends LitElement>(target: T, propertyKey: keyof T) => void;

export interface LitElementWithDisplayBox extends LitElement {
    displayBox?: "contents" | "block";
}

export interface IntersectionObserverDecoratorInit extends IntersectionObserverInit {
    /**
     * Whether to ascend the DOM tree to find a parent with a layout box (i.e. non "display: contents") and use that as the target for intersection checking.
     */
    useAncestorBox?: boolean;
}

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
 *
 * @attr display-box If set to "contents", the element will be considered intersecting.
 */
export function intersectionObserver({
    useAncestorBox: initialUseAncestorBox = false,
    ...init
}: IntersectionObserverDecoratorInit = {}): IntersectionDecorator {
    return <T extends LitElementWithDisplayBox, K extends keyof T>(target: T, key: K) => {
        //#region Prepare observer

        let useAncestorBox = initialUseAncestorBox;

        property({ attribute: false, useDefault: false })(target, key);

        const boxTargets = new WeakMap<T, Element>();

        function findAndCacheBoxTarget(instance: T): Element {
            let boxTarget = boxTargets.get(instance);

            if (!boxTarget) {
                boxTarget = findNearestBoxTarget(instance);
                boxTargets.set(instance, boxTarget);
            }

            return boxTarget;
        }

        const observerCallback: IntersectionObserverCallback = (entries) => {
            for (const entry of entries) {
                const currentTarget = entry.target as T;
                let intersecting = entry.isIntersecting;

                if (!intersecting && useAncestorBox) {
                    const boxTarget = findAndCacheBoxTarget(currentTarget);
                    intersecting = isInViewport(boxTarget);
                }

                const cachedIntersecting = currentTarget[key];

                if (cachedIntersecting !== intersecting) {
                    Object.assign(currentTarget, {
                        [key]: intersecting,
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

        const synchronizeUseAncestorBox = (nextDisplayBox?: "contents" | "block") => {
            useAncestorBox = nextDisplayBox === "contents" || initialUseAncestorBox;
        };

        /**
         * Applies the necessary lifecycle callback with access to protected properties of the target class.
         */
        function applyLifecycleCallbacks(this: T) {
            const { connectedCallback, disconnectedCallback, updated } = this;

            this.connectedCallback = function connectedCallbackWrapper(this: T) {
                connectedCallback?.call(this);

                synchronizeUseAncestorBox(this.displayBox);

                if (this.hasUpdated) {
                    observer.observe(this);
                } else {
                    this.updateComplete.then(() => {
                        observer.observe(this);
                    });
                }
            };

            this.disconnectedCallback = function disconnectedCallbackWrapper(
                this: LitElementWithDisplayBox,
            ) {
                disconnectedCallback?.call(this);

                if (observer) {
                    observer.disconnect();
                }
            };

            this.updated = function updatedWrapper(this: T, changedProperties: PropertyValues<T>) {
                updated?.call(this, changedProperties);

                if (changedProperties.has("displayBox")) {
                    synchronizeUseAncestorBox(this.displayBox);
                }
            };
        }

        applyLifecycleCallbacks.call(target);

        //#endregion
    };
}
