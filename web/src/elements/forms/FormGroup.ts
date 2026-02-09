import { AKElement } from "#elements/Base";
import Styles from "#elements/forms/FormGroup.css";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

/**
 * Form Group
 *
 * Mostly visual effects, with a single interaction for opening/closing the view.
 *
 * @todo Listen for custom events from its children about 'invalidation' events, and
 * trigger the `expanded` property as needed.
 */
@customElement("ak-form-group")
export class AKFormGroup extends AKElement {
    static styles: CSSResult[] = [PFForm, PFButton, PFFormControl, Styles];

    //region Properties

    @property({ type: Boolean, reflect: true })
    public open = false;

    @property({ type: String, reflect: true })
    public label = msg("Details");

    @property({ type: String, reflect: true })
    public description?: string;

    //#endregion

    //#region Lifecycle

    #invalidInputObserver: MutationObserver | null = null;

    /**
     * Explore within the form group for invalid inputs, revealing the first
     *
     * Note that this occurs **after** client-side validation, typically when
     * server-side updates the `errorMessages` property.
     */
    #explore = (mutations: MutationRecord[]) => {
        for (const mutation of mutations) {
            if (mutation.type !== "attributes") continue;

            const element = mutation.target as HTMLElement;

            if (element.getAttribute("aria-invalid") === "true" && !this.open) {
                this.open = true;

                requestAnimationFrame(() => element.focus());

                break;
            }
        }
    };

    public connectedCallback(): void {
        super.connectedCallback();

        this.#invalidInputObserver = new MutationObserver((mutations) => {
            // We wait for the next frame for a smoother experience.
            requestAnimationFrame(() => this.#explore(mutations));
        });

        this.#invalidInputObserver.observe(this, {
            subtree: true,
            attributes: true,
            attributeFilter: ["aria-invalid"],
        });
    }

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#invalidInputObserver?.disconnect();
        this.#invalidInputObserver = null;
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        const previousOpen = changedProperties.get("open");

        if (typeof previousOpen !== "boolean") return;

        if (this.open && this.open !== previousOpen) {
            cancelAnimationFrame(this.#scrollAnimationFrame);

            this.#scrollAnimationFrame = requestAnimationFrame(this.#scrollIntoView);
        }
    }

    #detailsRef = createRef<HTMLDetailsElement>();

    #scrollAnimationFrame = -1;

    #scrollIntoView = (): void => {
        this.#detailsRef.value?.scrollIntoView({
            behavior: "smooth",
        });
    };

    /**
     * Toggle the open state of the form group.
     */
    public toggle = (event: Event): void => {
        event.preventDefault();

        this.open = !this.open;
    };

    //#region Render

    public render(): TemplateResult {
        return html`
            <details
                ${ref(this.#detailsRef)}
                ?open=${this.open}
                aria-expanded=${this.open ? "true" : "false"}
                role="group"
                aria-labelledby="form-group-header-title"
                aria-describedby="form-group-expandable-content-description"
            >
                <summary @click=${this.toggle}>
                    <div class="pf-c-form__field-group-header-main">
                        <header class="pf-c-form__field-group-header-title">
                            <div
                                class="pf-c-form__field-group-header-title-text"
                                id="form-group-header-title"
                                role="heading"
                                aria-level="3"
                            >
                                ${this.label}
                                <slot name="header"></slot>
                            </div>
                        </header>

                        <div
                            class="pf-c-form__field-group-header-description"
                            data-test-id="form-group-header-description"
                            id="form-group-expandable-content-description"
                        >
                            ${this.description}
                            <slot name="description"></slot>
                        </div>
                    </div>
                </summary>
                <div id="form-group-expandable-content">
                    <slot></slot>
                </div>
            </details>
        `;
    }

    //#endregion
}

//#region Utilities

/**
 * Deeply report the validity of the form, expanding collapsed groups as needed
 * to reveal invalid inputs.
 *
 * @param form The form element to check.
 * @returns Whether the form is valid.
 */
export function reportValidityDeep(
    form: Pick<HTMLFormElement, "checkValidity" | "reportValidity" | "querySelector">,
): boolean {
    // Invalid inputs within collapsed groups can't receive focus,
    // so we need to check validity before reporting.
    const valid = form.checkValidity();

    if (!valid) {
        // We only want to reveal the first invalid input to avoid
        // a rollercoaster of form groups attempting to scroll into view.
        const formGroup = form.querySelector<AKFormGroup>(
            "ak-form-group:not([open]):has(input:invalid)",
        );

        if (formGroup) {
            formGroup.open = true;
            // Ensure the form group has a frame to reveal the invalid input.
            requestAnimationFrame(() => form.reportValidity());

            return false;
        }
    }

    // Otherwise, we're ready to use the browser's native validation.
    return form.reportValidity();
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-group": AKFormGroup;
    }
}
