import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Form Group
 *
 * Mostly visual effects, with a single interaction for opening/closing the view.
 *
 * @todo Can we use `<details>` element to make this more a11y friendly?
 * @todo Listen for custom events from its children about 'invalidation' events, and
 * trigger the `expanded` property as needed.
 */
@customElement("ak-form-group")
export class AKFormGroup extends AKElement {
    @property({ type: Boolean, reflect: true })
    public open = false;

    @property({ type: String, reflect: true })
    public label = msg("Details");

    @property({ type: String, reflect: true })
    public description?: string;

    static styles: CSSResult[] = [
        PFBase,
        PFForm,
        PFButton,
        PFFormControl,

        css`
            :host {
                --marker-color: var(--pf-global--Color--200);
                --marker-color-hover: var(--pf-global--Color--100);
            }

            .pf-c-form__field-group-header-description {
                text-wrap: balance;
            }

            details {
                &::details-content {
                    height: 0;
                    overflow: clip;
                    transition-behavior: normal, allow-discrete;
                    transition-duration: var(--pf-global--TransitionDuration);
                    transition-timing-function: var(--pf-global--TimingFunction);
                    transition-property: height, content-visibility;

                    @media (prefers-reduced-motion) {
                        transition-duration: 0;
                    }
                }

                @supports (interpolate-size: allow-keywords) {
                    interpolate-size: allow-keywords;

                    &[open]::details-content {
                        height: auto;
                    }
                }

                &::details-content {
                    padding-inline-start: var(
                        --pf-c-form__field-group--GridTemplateColumns--toggle
                    );
                }

                & > summary {
                    list-style-position: outside;
                    margin-inline-start: 2em;
                    padding-inline-start: calc(var(--pf-global--spacer--md) + 0.25rem);
                    padding: var(--pf-global--spacer--md);
                    list-style-type: "\\f105";
                    cursor: pointer;
                    user-select: none;

                    &::marker {
                        color: var(--marker-color);
                        transition: var(--pf-c-form__field-group-toggle-icon--Transition);
                        font-family: "Font Awesome 5 Free";
                        font-weight: 900;
                    }

                    &:hover::marker {
                        outline: 1px dashed red;
                        color: var(--marker-color-hover);
                    }
                }

                &[open] summary {
                    list-style-type: "\\f107";
                }
            }
        `,
    ];

    formRef = createRef<HTMLFormElement>();

    scrollAnimationFrame = -1;

    scrollIntoView = (): void => {
        this.formRef.value?.scrollIntoView({
            behavior: "smooth",
        });
    };

    /**
     * Toggle the open state of the form group.
     */
    public toggle = (event: Event): void => {
        event.preventDefault();
        cancelAnimationFrame(this.scrollAnimationFrame);

        this.open = !this.open;

        if (this.open) {
            this.scrollAnimationFrame = requestAnimationFrame(this.scrollIntoView);
        }
    };

    public render(): TemplateResult {
        return html`
            <details
                ${ref(this.formRef)}
                ?open=${this.open}
                ?aria-expanded="${this.open}"
                role="group"
                aria-owns="form-group-expandable-content"
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
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-group": AKFormGroup;
    }
}
