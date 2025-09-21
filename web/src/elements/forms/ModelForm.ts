/* eslint-disable @typescript-eslint/no-explicit-any */
import "#elements/EmptyState";

import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { ErrorProp } from "#components/ak-field-errors";

import { msg } from "@lit/localize";
import { html, LitElement, nothing, PropertyValues } from "lit";
import { property, state } from "lit/decorators.js";

/**
 * Options for configuring the IntersectionObserver
 */
export interface IntersectionObserverOptions {
    /**
     * The root element for the observer. Defaults to the viewport.
     */
    root?: Element | Document | null;

    /**
     * Margin around the root. Can be specified like CSS margin.
     * E.g., "10px 20px 30px 40px" (top, right, bottom, left)
     */
    rootMargin?: string;

    /**
     * Either a single number or an array of numbers between 0.0 and 1.0,
     * specifying the percentage of the target's visibility the observer's
     * callback should be executed.
     */
    threshold?: number | number[];

    /**
     * If true, the observer will disconnect after the first intersection
     */
    once?: boolean;

    /**
     * Custom callback to handle intersection changes
     */
    onIntersection?: (isIntersecting: boolean, entry: IntersectionObserverEntry) => void;
}

/**
 * WeakMap to store observer instances for each element
 */
const observerMap = new WeakMap<Element, IntersectionObserver>();

/**
 * Type for the decorator
 */
type IntersectionDecorator = (target: LitElement, propertyKey: string | symbol) => void;

/**
 * A decorator that applies an IntersectionObserver to the element.
 * This is useful for lazy-loading elements that are not visible on the screen.
 *
 * @param options - Configuration options for the IntersectionObserver
 *
 * @example
 * ```ts
 * class MyElement extends LitElement {
 *     @intersectionObserver()
 *     protected visible!: boolean;
 *
 *     @intersectionObserver({ threshold: 0.5, rootMargin: '50px' })
 *     protected halfVisible!: boolean;
 *
 *     @intersectionObserver({
 *         once: true,
 *         onIntersection: (isIntersecting) => {
 *             if (isIntersecting) {
 *                 console.log('Element is now visible!');
 *             }
 *         }
 *     })
 *     protected hasBeenVisible!: boolean;
 *
 *     render() {
 *         if (!this.visible) return nothing;
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
export function intersectionObserver(
    options: IntersectionObserverOptions = {},
): IntersectionDecorator {
    return (target: any, propertyKey: string | symbol) => {
        const key = String(propertyKey);

        // Create a unique symbol for storing the actual value
        const privateKey = Symbol(`__${key}`);

        // Apply the @property decorator to make it reactive
        property({ type: Boolean, attribute: false })(target, key);

        // Store the original connectedCallback and disconnectedCallback
        const originalConnectedCallback = target.connectedCallback;
        const originalDisconnectedCallback = target.disconnectedCallback;
        const originalUpdated = target.updated;

        // Override connectedCallback to set up the observer
        target.connectedCallback = function (this: LitElement) {
            originalConnectedCallback?.call(this);

            // Initialize the property to false
            (this as any)[privateKey] = false;
            (this as any)[key] = false;

            // Create the observer
            const observerOptions: IntersectionObserverInit = {
                root: options.root || null,
                rootMargin: options.rootMargin || "0px",
                threshold: options.threshold ?? 0,
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    const isIntersecting = entry.isIntersecting;
                    const currentValue = (this as any)[key];

                    // Only update if the value has changed
                    if (currentValue !== isIntersecting) {
                        (this as any)[privateKey] = isIntersecting;
                        (this as any)[key] = isIntersecting;

                        // Call custom callback if provided
                        if (options.onIntersection) {
                            options.onIntersection(isIntersecting, entry);
                        }

                        // Request an update to trigger re-render
                        this.requestUpdate(key, currentValue);
                    }

                    // Disconnect if once option is true and element is intersecting
                    if (options.once && isIntersecting) {
                        observer.disconnect();
                        observerMap.delete(this);
                    }
                });
            }, observerOptions);

            // Store the observer
            observerMap.set(this, observer);

            // Start observing after the element has been rendered
            // We need to wait for the first update to ensure the element is in the DOM
            const waitForFirstUpdate = () => {
                if (this.hasUpdated) {
                    observer.observe(this);
                } else {
                    // If not yet updated, wait for the first update
                    this.updateComplete.then(() => {
                        observer.observe(this);
                    });
                }
            };

            waitForFirstUpdate();
        };

        // Override disconnectedCallback to clean up the observer
        target.disconnectedCallback = function (this: LitElement) {
            originalDisconnectedCallback?.call(this);

            // Clean up the observer
            const observer = observerMap.get(this);
            if (observer) {
                observer.disconnect();
                observerMap.delete(this);
            }
        };

        // Define the property getter and setter
        Object.defineProperty(target, key, {
            get(this: LitElement) {
                return (this as any)[privateKey] ?? false;
            },
            set(this: LitElement, value: boolean) {
                const oldValue = (this as any)[privateKey];
                (this as any)[privateKey] = value;
                this.requestUpdate(key, oldValue);
            },
            enumerable: true,
            configurable: true,
        });
    };
}

/**
 * Helper function to manually trigger observation of an element
 * Useful for programmatically starting observation
 */
export function observeElement(
    element: Element,
    options: IntersectionObserverOptions = {},
): () => void {
    const observerOptions: IntersectionObserverInit = {
        root: options.root || null,
        rootMargin: options.rootMargin || "0px",
        threshold: options.threshold ?? 0,
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (options.onIntersection) {
                options.onIntersection(entry.isIntersecting, entry);
            }

            if (options.once && entry.isIntersecting) {
                observer.disconnect();
            }
        });
    }, observerOptions);

    observer.observe(element);

    // Return cleanup function
    return () => observer.disconnect();
}

/**
 * A base form that automatically tracks the server-side object (instance)
 * that we're interested in.  Handles loading and tracking of the instance.
 */
export abstract class ModelForm<T, PKT extends string | number = string | number> extends Form<T> {
    @intersectionObserver()
    public visible!: boolean;

    public get hidden(): boolean {
        return !this.visible;
    }

    public get ariaHidden(): string {
        return this.visible ? "false" : "true";
    }

    //#region Properties

    @property({ attribute: false })
    public instancePk: PKT | null = null;

    @property({ attribute: false })
    public instance: T | null = this.defaultInstance;

    //#endregion

    //#region Lifecycle

    @state()
    protected error: ErrorProp | null = null;

    @state()
    protected loading = false;

    /**
     * An overridable method for loading an instance.
     *
     * @param pk The primary key of the instance to load.
     * @returns A promise that resolves to the loaded instance.
     */
    protected abstract loadInstance(pk: PKT): Promise<T>;

    /**
     * An overridable method for loading any data, beyond the instance.
     *
     * @see {@linkcode loadInstance}
     * @returns A promise that resolves when the data has been loaded.
     */
    protected load?(): Promise<void>;

    #refresh = (): Promise<void> => {
        if (!this.instancePk && typeof this.instancePk !== "number") {
            return Promise.resolve();
        }

        this.loading = true;

        const loadPromise = this.load?.() ?? Promise.resolve();

        return loadPromise
            .then(() => {
                if (!this.instancePk && typeof this.instancePk !== "number") {
                    return Promise.resolve(null);
                }

                return this.loadInstance(this.instancePk);
            })
            .then((instance) => {
                this.instance = instance;
            })
            .catch(async (error: unknown) => {
                this.error = await parseAPIResponseError(error);
            })
            .finally(() => {
                this.loading = false;
                this.requestUpdate();
            });
    };

    public updated(changedProperties: PropertyValues<this>): void {
        const previousVisibility = changedProperties.get("visible");

        if (typeof previousVisibility !== "boolean") return;

        if (this.visible && this.visible !== previousVisibility) {
            this.#refresh();
        }
    }

    protected get defaultInstance(): T | null {
        return null;
    }

    // constructor() {
    //     super();

    //     this.addEventListener(EVENT_REFRESH, this.#refresh);
    // }

    /**
     * Render the error state.
     *
     * @abstract
     */
    protected renderError(): SlottedTemplateResult {
        if (!this.error) return nothing;

        return html`<ak-empty-state icon="fa-ban"
            ><span>${msg("Failed to fetch model.")}</span>
            <div>${pluckErrorDetail(this.error)}</div>
        </ak-empty-state>`;
    }

    render(): SlottedTemplateResult {
        if (!this.visible) return nothing;

        if (this.error) {
            return this.renderError();
        }

        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        return super.render();
    }
}
