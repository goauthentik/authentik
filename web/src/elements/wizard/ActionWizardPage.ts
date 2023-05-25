import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { WizardAction } from "@goauthentik/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFProgressStepper from "@patternfly/patternfly/components/ProgressStepper/progress-stepper.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ResponseError } from "@goauthentik/api";

export enum ActionState {
    pending = "pending",
    running = "running",
    done = "done",
    failed = "failed",
}

export interface ActionStateBundle {
    action: WizardAction;
    state: ActionState;
    idx: number;
}

@customElement("ak-wizard-page-action")
export class ActionWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFBullseye, PFEmptyState, PFTitle, PFProgressStepper];
    }

    @property({ attribute: false })
    states: ActionStateBundle[] = [];

    @property({ attribute: false })
    currentStep?: ActionStateBundle;

    activeCallback = async (): Promise<void> => {
        this.states = [];
        this.host.actions.map((act, idx) => {
            this.states.push({
                action: act,
                state: ActionState.pending,
                idx: idx,
            });
        });
        this.host.canBack = false;
        this.host.canCancel = false;
        await this.run();
        // Ensure wizard is closable, even when run() failed
        this.host.isValid = true;
    };

    sidebarLabel = () => msg("Apply changes");

    async run(): Promise<void> {
        this.currentStep = this.states[0];
        await new Promise((r) => setTimeout(r, 500));
        for await (const bundle of this.states) {
            this.currentStep = bundle;
            this.currentStep.state = ActionState.running;
            this.requestUpdate();
            try {
                await bundle.action.run();
                await new Promise((r) => setTimeout(r, 500));
                this.currentStep.state = ActionState.done;
                this.requestUpdate();
            } catch (exc) {
                if (exc instanceof ResponseError) {
                    this.currentStep.action.subText = await exc.response.text();
                } else {
                    this.currentStep.action.subText = (exc as Error).toString();
                }
                this.currentStep.state = ActionState.failed;
                this.requestUpdate();
                return;
            }
        }
        this.host.isValid = true;
        this.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            }),
        );
    }

    render(): TemplateResult {
        return html`<div class="pf-l-bullseye">
            <div class="pf-c-empty-state pf-m-lg">
                <div class="pf-c-empty-state__content">
                    <i class="fas fa- fa-cogs pf-c-empty-state__icon" aria-hidden="true"></i>
                    <h1 class="pf-c-title pf-m-lg">${this.currentStep?.action.displayName}</h1>
                    <div class="pf-c-empty-state__body">
                        <ol class="pf-c-progress-stepper pf-m-vertical">
                            ${this.states.map((state) => {
                                let cls = "";
                                switch (state.state) {
                                    case ActionState.pending:
                                        cls = "pf-m-pending";
                                        break;
                                    case ActionState.done:
                                        cls = "pf-m-success";
                                        break;
                                    case ActionState.running:
                                        cls = "pf-m-info";
                                        break;
                                    case ActionState.failed:
                                        cls = "pf-m-danger";
                                        break;
                                }
                                if (state.idx === this.currentStep?.idx) {
                                    cls += " pf-m-current";
                                }
                                return html` <li class="pf-c-progress-stepper__step ${cls}">
                                    <div class="pf-c-progress-stepper__step-connector">
                                        <span class="pf-c-progress-stepper__step-icon">
                                            <i class="fas fa-check-circle" aria-hidden="true"></i>
                                        </span>
                                    </div>
                                    <div class="pf-c-progress-stepper__step-main">
                                        <div class="pf-c-progress-stepper__step-title">
                                            ${state.action.displayName}
                                        </div>
                                        ${state.action.subText
                                            ? html`<div
                                                  class="pf-c-progress-stepper__step-description"
                                              >
                                                  ${state.action.subText}
                                              </div>`
                                            : html``}
                                    </div>
                                </li>`;
                            })}
                        </ol>
                    </div>
                </div>
            </div>
        </div>`;
    }
}
