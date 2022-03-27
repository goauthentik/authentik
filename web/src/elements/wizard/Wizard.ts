import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { property } from "@lit/reactive-element/decorators/property.js";
import { CSSResult, TemplateResult, html } from "lit";
import { cache } from "lit/directives/cache.js";

import PFWizard from "@patternfly/patternfly/components/Wizard/wizard.css";

import { ModalButton } from "../buttons/ModalButton";
import { WizardStep } from "./WizardStep";
import { WizardStepContainer } from "./WizardStepContainer";

@customElement("ak-wizard")
export class Wizard extends ModalButton implements WizardStepContainer {
    @property()
    header?: string;

    @property()
    description?: string;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFWizard);
    }

    @property({ attribute: false })
    steps: WizardStep[] = [];

    set currentStep(value: WizardStep) {
        this._currentStep = value;
        this._currentStep.host = this;
        this._currentStep.activeCallback();
    }

    get currentStep(): WizardStep {
        return this._currentStep;
    }

    @property({ attribute: false })
    _currentStep!: WizardStep;

    finalHandler?: () => Promise<void>;

    setSteps(...steps: WizardStep[]): void {
        this.steps = steps;
        this.requestUpdate();
    }

    renderModalInner(): TemplateResult {
        if (!this.currentStep) {
            this.currentStep = this.steps[0];
        }
        const currentIndex = this.steps.indexOf(this.currentStep);
        return html`<div class="pf-c-wizard">
            <div class="pf-c-wizard__header">
                <button
                    class="pf-c-button pf-m-plain pf-c-wizard__close"
                    type="button"
                    aria-label="${t`Close`}"
                >
                    <i class="fas fa-times" aria-hidden="true"></i>
                </button>
                <h1 class="pf-c-title pf-m-3xl pf-c-wizard__title">${this.header}</h1>
                <p class="pf-c-wizard__description">${this.description}</p>
            </div>
            <div class="pf-c-wizard__outer-wrap">
                <div class="pf-c-wizard__inner-wrap">
                    <nav class="pf-c-wizard__nav">
                        <ol class="pf-c-wizard__nav-list">
                            ${this.steps.map((step, idx) => {
                                const currentIdx = this.steps.indexOf(this.currentStep);
                                return html`
                                    <li class="pf-c-wizard__nav-item">
                                        <button
                                            class="pf-c-wizard__nav-link ${idx === currentIdx
                                                ? "pf-m-current"
                                                : ""}"
                                            ?disabled=${this.steps.indexOf(this.currentStep) < idx}
                                            @click=${() => {
                                                this.currentStep = step;
                                            }}
                                        >
                                            ${step.renderNavList()}
                                        </button>
                                    </li>
                                `;
                            })}
                        </ol>
                    </nav>
                    <main class="pf-c-wizard__main">
                        <div class="pf-c-wizard__main-body">
                            ${cache(this.currentStep.render())}
                        </div>
                    </main>
                </div>
                <footer class="pf-c-wizard__footer">
                    <button
                        class="pf-c-button pf-m-primary"
                        type="submit"
                        ?disabled=${!this._currentStep.isValid()}
                        @click=${async () => {
                            const cb = await this.currentStep.nextCallback();
                            if (!cb) {
                                return;
                            }
                            if (currentIndex === this.steps.length - 1) {
                                if (this.finalHandler) {
                                    await this.finalHandler();
                                }
                                this.open = false;
                            } else {
                                this.currentStep = this.steps[currentIndex + 1];
                            }
                        }}
                    >
                        ${currentIndex === this.steps.length - 1 ? t`Finish` : t`Next`}
                    </button>
                    ${this.steps.indexOf(this.currentStep) > 0
                        ? html`
                              <button
                                  class="pf-c-button pf-m-secondary"
                                  type="button"
                                  @click=${() => {
                                      this.currentStep = this.steps[currentIndex - 1];
                                  }}
                              >
                                  ${t`Back`}
                              </button>
                          `
                        : html``}
                    <div class="pf-c-wizard__footer-cancel">
                        <button
                            class="pf-c-button pf-m-link"
                            type="button"
                            @click=${() => {
                                this.open = false;
                                this.currentStep = this.steps[0];
                            }}
                        >
                            ${t`Cancel`}
                        </button>
                    </div>
                </footer>
            </div>
        </div>`;
    }
}
