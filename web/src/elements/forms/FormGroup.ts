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
 * @todo Listen for custom events from its children about 'invalidation' events, and
 * trigger the `expanded` property as needed.
 */
@customElement("ak-form-group")
export class FormGroup extends AKElement {
    @property({ type: Boolean, reflect: true })
    expanded = false;

    @property({ type: String, attribute: "aria-label", reflect: true })
    ariaLabel = msg("Details");

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFForm,
            PFButton,
            PFFormControl,
            css`
                /**
                 * Workaround to trigger the hover effect on the button when the header is hovered.
                 *
                 * Alternatively, we group the expander button and header, but the grid would have to be
                 * restructured to allow for this.
                 */
                .pf-c-form__field-group:has(.pf-c-form__field-group-header:hover) .pf-c-button {
                    color: var(--pf-global--Color--100) !important;
                }

                /**
                 * Transition ensuring a smooth animation when the body is expanded/collapsed.
                 */
                slot[name="body"] {
                    transition-behavior: allow-discrete;
                    transition-property: opacity, display, transform;
                    transition-duration: var(--pf-global--TransitionDuration);
                    transition-timing-function: var(--pf-global--TimingFunction);
                    display: block;
                    opacity: 1;
                    transform: scaleY(1);
                    transform-origin: top left;
                    will-change: opacity, display, transform;
                }

                slot[name="body"][hidden] {
                    opacity: 0 !important;
                    display: none !important;
                    transform: scaleY(0) !important;
                }

                @media (prefers-reduced-motion) {
                    slot[name="body"] {
                        transition-duration: 0s;
                    }
                }
            `,
        ];
    }

    formRef = createRef<HTMLFormElement>();

    scrollAnimationFrame = -1;

    scrollIntoView = (): void => {
        this.formRef.value?.scrollIntoView({
            behavior: "smooth",
        });
    };

    toggleExpanded = (): void => {
        cancelAnimationFrame(this.scrollAnimationFrame);

        this.expanded = !this.expanded;

        if (this.expanded) {
            this.scrollAnimationFrame = requestAnimationFrame(this.scrollIntoView);
        }
    };

    render(): TemplateResult {
        return html`<div class="pf-c-form" ${ref(this.formRef)}>
            <div class="pf-c-form__field-group ${this.expanded ? "pf-m-expanded" : ""}">
                <div class="pf-c-form__field-group-toggle">
                    <div class="pf-c-form__field-group-toggle-button">
                        <button
                            class="pf-c-button pf-m-plain"
                            type="button"
                            aria-expanded="${this.expanded}"
                            aria-label=${this.ariaLabel}
                            @click=${this.toggleExpanded}
                        >
                            <span class="pf-c-form__field-group-toggle-icon">
                                <i class="fas fa-angle-right" aria-hidden="true"></i>
                            </span>
                        </button>
                    </div>
                </div>
                <div
                    class="pf-c-form__field-group-header pf-m-pressable"
                    @click=${this.toggleExpanded}
                    aria-expanded=${this.expanded}
                    aria-role="button"
                >
                    <div class="pf-c-form__field-group-header-main">
                        <div class="pf-c-form__field-group-header-title">
                            <div class="pf-c-form__field-group-header-title-text">
                                <slot name="header"></slot>
                            </div>
                        </div>
                        <div class="pf-c-form__field-group-header-description">
                            <slot name="description"></slot>
                        </div>
                    </div>
                </div>
                <slot
                    ?hidden=${!this.expanded}
                    class="pf-c-form__field-group-body"
                    name="body"
                ></slot>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-group": FormGroup;
    }
}
