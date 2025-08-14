import { createMixin } from "#elements/types";

import { property } from "lit/decorators.js";

/**
 * A mixin that provides form-associated internals to the element.
 *
 * @see {@link https://developer.mozilla.org/en-US/docs/Web/API/ElementInternals | MDN}
 *
 * @see {@linkcode WithInternals}
 */
export interface InternalsMixin
    extends Pick<
        ElementInternals,
        | "form"
        | "validity"
        | "validationMessage"
        | "willValidate"
        | "labels"
        | "checkValidity"
        | "reportValidity"
    > {
    internals: ElementInternals;

    /**
     * The name of the input, provided to the form.
     */
    name: string | null;

    /**
     * The type of the input, provided to the form.
     */
    type: string;

    /**
     * Whether or not the input is required.
     */
    required?: boolean;

    /**
     * Whether or not the input is read-only.
     */
    readonly?: boolean;
}

/**
 * A mixin that provides form-associated internals to the element.
 *
 * @see {@linkcode InternalsMixin}
 * @see {@linkcode https://developer.mozilla.org/en-US/docs/Web/API/ElementInternals | MDN}
 *
 * @category Mixin
 */
export const WithInternals = createMixin<InternalsMixin>(
    ({
        // ---
        SuperClass,
    }) => {
        abstract class InternalsProvider extends SuperClass implements InternalsMixin {
            static readonly formAssociated = true;

            internals = this.attachInternals();

            //#region Properties

            @property({ type: Boolean })
            public required?: boolean;

            @property({ type: Boolean })
            public readonly?: boolean;

            public get form(): HTMLFormElement | null {
                return this.internals.form;
            }

            public get name() {
                return this.getAttribute("name");
            }

            public get type() {
                return this.localName;
            }

            public get validity() {
                return this.internals.validity;
            }

            public get validationMessage() {
                return this.internals.validationMessage;
            }

            public get willValidate() {
                return this.internals.willValidate;
            }

            public get labels() {
                return this.internals.labels;
            }

            public checkValidity() {
                return this.internals.checkValidity();
            }

            public reportValidity() {
                return this.internals.reportValidity();
            }

            //#endregion
        }

        return InternalsProvider;
    },
);
