import { checkObjectShallowEquality } from "#common/collections";

import { AKElement } from "#elements/Base";
import { asInvoker, type ModalTemplate } from "#elements/dialogs/invokers";
import type { DialogInit, TransclusionElementConstructor } from "#elements/dialogs/shared";
import type { LitPropertyRecord } from "#elements/types";
import { isAKElementConstructor, StrictUnsafe } from "#elements/utils/unsafe";

import { ElementPart, noChange } from "lit";
import {
    directive,
    Directive,
    DirectiveResult,
    PartInfo,
    PartType,
} from "lit-html/async-directive.js";

//#region Directives

type ModalDirectiveParameters = [
    factory: ModalTemplate | CustomElementConstructor,
    props?: LitPropertyRecord<object> | null,
    options?: DialogInit,
];

/**
 * A directive that manages the event listener for an invoker function created by {@linkcode asInvoker}.
 *
 * Supports memoization via an optional `deps` array in the options object. When `deps` is provided,
 * the directive will skip rebinding the event listener if all dep values are shallowly equal to the
 * previous render. If `deps` is omitted, the listener rebinds on every update (safe default).
 *
 * @see {@linkcode asInvoker} for the underlying invoker.
 * @see {@linkcode modalInvoker} for the Lit HTML variation.
 */
export class ModalInvokerDirective extends Directive {
    constructor(partInfo: PartInfo) {
        super(partInfo);

        if (partInfo.type !== PartType.ELEMENT) {
            throw new Error("modalInvoker() can only be used on an element");
        }
    }

    #cleanup: (() => void) | null = null;
    #prevProps: LitPropertyRecord<object> | null = null;

    public update(part: ElementPart, [factory, props, options]: ModalDirectiveParameters): void {
        if (props && checkObjectShallowEquality(props, this.#prevProps)) {
            // Skip rebind
            return;
        }

        // Tear down old listener before rebinding
        if (this.#cleanup) {
            this.#cleanup();
            this.#cleanup = null;
        }

        const listener = asInvoker(
            (event) => {
                if (!isAKElementConstructor(factory)) {
                    return (factory as ModalTemplate)(event);
                }

                const tagName = window.customElements.getName(factory);

                if (!tagName) {
                    throw new TypeError("Provided constructor is not a registered custom element");
                }

                return StrictUnsafe(
                    tagName,
                    props as unknown as LitPropertyRecord<ModelFormLikeConstructor>,
                );
            },
            { ...options, invokerElement: part.element },
        );
        part.element.addEventListener("click", listener);

        const cleanup = () => {
            part.element.removeEventListener("click", listener);
            // Null out prevDeps so that the next render cycle always rebinds.
            // This handles the case where an AbortSignal fires between renders.
            this.#prevProps = null;
        };

        if (options?.signal) {
            options.signal.addEventListener("abort", cleanup, { once: true });
        }

        this.#cleanup = cleanup;
        this.#prevProps = props ?? null;
    }

    render(..._args: ModalDirectiveParameters) {
        return noChange;
    }
}

export type ModalInvokerDirectiveResult = DirectiveResult<typeof ModalInvokerDirective>;

export type ModalInvoker = <T extends ModalTemplate | TransclusionElementConstructor>(
    factory: T,
    /**
     * Optional props to pass to the custom element constructor when the factory is a constructor.
     * Ignored if the factory is a ModalTemplate function.
     */
    props?: T extends TransclusionElementConstructor
        ? LitPropertyRecord<InstanceType<T>> | null
        : null,
    options?: DialogInit,
) => ModalInvokerDirectiveResult;

/**
 * A Lit HTML directive that can be used to attach a modal invoker to an element.
 *
 * ```ts
 * html`<button ${modalInvoker(SomeModalConstructor)}>Open</button>`
 * ```
 */
export const modalInvoker = directive(ModalInvokerDirective) as ModalInvoker;
//#region Model Forms

export interface ModelFormLike {
    instancePk?: string | number | null;
}

export interface ModelFormLikeConstructor extends CustomElementConstructor {
    new (): ModelFormLike;
}

/**
 * A helper function to create a modal invoker for editing an instance of a form-like element.
 *
 * @remarks
 * This is defined externally from the form itself to allow existing forms to
 * easily add edit invokers without needing to extend a specific base class.
 */
export function asInstanceInvoker<T extends ModelFormLikeConstructor>(
    this: T,
    instancePk?: string | number | null,
    props?: LitPropertyRecord<InstanceType<T>> | null,
    init?: DialogInit,
): ModalInvokerDirectiveResult {
    const mergedProps: LitPropertyRecord<ModelFormLikeConstructor> = { instancePk, ...props };

    return modalInvoker(this, mergedProps as unknown as undefined, init);
}

/**
 * Given a tag name, looks up the corresponding custom element constructor and returns it.
 *
 * @throws {TypeError} If no custom element is defined for the given tag name.
 * @param tagName The tag name of the custom element to look up.
 * @returns The custom element constructor associated with the given tag name.
 */
export function lookupElementConstructor<T extends CustomElementConstructor>(
    tagName: string,
    registry: CustomElementRegistry = window.customElements,
): T {
    const ElementConstructor = registry.get(tagName);

    if (!ElementConstructor) {
        throw new TypeError(`No custom element defined for tag name: ${tagName}`);
    }

    return ElementConstructor as unknown as T;
}

/**
 * A helper function to create a modal invoker for editing an instance of a form-like element,
 * given the tag name of the custom element.
 *
 * This is a convenience wrapper around {@linkcode asEditModalInvoker}
 * that performs a lookup of the custom element constructor based on the provided tag name.
 */
export function asInstanceInvokerByTagName<T extends AKElement>(
    tagName: string,
    instancePk?: string | number | null,
    props?: LitPropertyRecord<T>,
    init?: DialogInit,
): ModalInvokerDirectiveResult {
    const ElementConstructor = lookupElementConstructor<ModelFormLikeConstructor>(tagName);

    return asInstanceInvoker.call(ElementConstructor, instancePk, props, init);
}
