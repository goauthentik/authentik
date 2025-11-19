import "#elements/EmptyState";
import "#elements/Expand";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_FLOW_ADVANCE, EVENT_FLOW_INSPECTOR_TOGGLE } from "#common/constants";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import Styles from "#flow/FlowInspector.css";

import { FlowInspection, FlowsApi, Stage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFNotificationDrawer from "@patternfly/patternfly/components/NotificationDrawer/notification-drawer.css";
import PFProgressStepper from "@patternfly/patternfly/components/ProgressStepper/progress-stepper.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

function stringify(obj: unknown): string {
    return JSON.stringify(obj, null, 4);
}

@customElement("ak-flow-inspector")
export class FlowInspector extends AKElement {
    @property({ type: String, attribute: "slug", useDefault: true })
    public flowSlug: string = window.location.pathname.split("/")[3];

    @property({ attribute: false })
    state?: FlowInspection;

    @property({ attribute: false })
    error?: APIError;

    static styles: CSSResult[] = [
        PFBase,
        PFButton,
        PFStack,
        PFCard,
        PFNotificationDrawer,
        PFDescriptionList,
        PFProgressStepper,
        Styles,
    ];

    constructor() {
        super();
        window.addEventListener(EVENT_FLOW_ADVANCE, this.advanceHandler as EventListener);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_FLOW_ADVANCE, this.advanceHandler as EventListener);
    }

    advanceHandler = (): void => {
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInspectorGet({
                flowSlug: this.flowSlug || "",
            })
            .then((state) => {
                this.error = undefined;
                this.state = state;
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);

                this.error = parsedError;
            });
    };

    // getStage return a stage without flowSet, for brevity
    getStage(stage?: Stage): unknown {
        if (!stage) {
            return stage;
        }
        delete stage.flowSet;
        return stage;
    }

    protected renderHeader() {
        return html`<div class="pf-c-notification-drawer__header">
            <div class="text">
                <h1 class="pf-c-notification-drawer__header-title">${msg("Flow inspector")}</h1>
            </div>
            <div class="pf-c-notification-drawer__header-action">
                <div class="pf-c-notification-drawer__header-action-close">
                    <button
                        @click=${() => {
                            window.dispatchEvent(
                                new CustomEvent(EVENT_FLOW_INSPECTOR_TOGGLE, {
                                    bubbles: true,
                                    composed: true,
                                }),
                            );
                        }}
                        class="pf-c-button pf-m-plain"
                        type="button"
                        aria-label=${msg("Close flow inspector")}
                    >
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                </div>
            </div>
        </div>`;
    }

    protected renderAccessDenied(): TemplateResult {
        return html`<aside
            aria-label=${msg("Flow inspector")}
            class="pf-c-drawer__body pf-m-no-padding"
        >
            <div class="pf-c-notification-drawer">
                ${this.renderHeader()}
                <div class="pf-c-notification-drawer__body">
                    <div class="pf-l-stack pf-m-gutter">
                        <div class="pf-l-stack__item">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">${pluckErrorDetail(this.error)}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </aside>`;
    }

    protected renderNextStage({ currentPlan, isCompleted }: FlowInspection): TemplateResult {
        return html`<div class="pf-c-card">
            <fieldset>
                <legend class="pf-c-card__title">${msg("Next stage")}</legend>
                <div class="pf-c-card__body">
                    <dl class="pf-c-description-list">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Stage name")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${currentPlan?.nextPlannedStage?.stageObj?.name || "-"}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Stage kind")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                <div class="pf-c-description-list__text">
                                    ${currentPlan?.nextPlannedStage?.stageObj?.verboseName || "-"}
                                </div>
                            </dd>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                <span class="pf-c-description-list__text"
                                    >${msg("Stage object")}</span
                                >
                            </dt>
                            <dd class="pf-c-description-list__description">
                                ${isCompleted
                                    ? html`<div class="pf-c-description-list__text">
                                          ${msg("This flow is completed.")}
                                      </div>`
                                    : html`<ak-expand>
                                          <pre class="pf-c-description-list__text">
${stringify(this.getStage(currentPlan?.nextPlannedStage?.stageObj))}</pre
                                          >
                                      </ak-expand>`}
                            </dd>
                        </div>
                    </dl>
                </div>
            </fieldset>
        </div>`;
    }

    protected renderPlanHistory({
        plans,
        isCompleted,
        currentPlan,
    }: FlowInspection): TemplateResult {
        return html`<div class="pf-c-card">
            <fieldset>
                <legend class="pf-c-card__title">${msg("Plan history")}</legend>
                <div class="pf-c-card__body">
                    <ol class="pf-c-progress-stepper pf-m-vertical">
                        ${plans.map((plan) => {
                            return html`<li class="pf-c-progress-stepper__step pf-m-success">
                                <div class="pf-c-progress-stepper__step-connector">
                                    <span class="pf-c-progress-stepper__step-icon">
                                        <i class="fas fa-check-circle" aria-hidden="true"></i>
                                    </span>
                                </div>
                                <div class="pf-c-progress-stepper__step-main">
                                    <div class="pf-c-progress-stepper__step-title">
                                        ${plan.currentStage.stageObj?.name}
                                    </div>
                                    <div class="pf-c-progress-stepper__step-description">
                                        ${plan.currentStage.stageObj?.verboseName}
                                    </div>
                                </div>
                            </li> `;
                        })}
                        ${currentPlan?.currentStage && !isCompleted
                            ? html`<li class="pf-c-progress-stepper__step pf-m-current pf-m-info">
                                  <div class="pf-c-progress-stepper__step-connector">
                                      <span class="pf-c-progress-stepper__step-icon">
                                          <i
                                              class="pficon pf-icon-resources-full"
                                              aria-hidden="true"
                                          ></i>
                                      </span>
                                  </div>
                                  <div class="pf-c-progress-stepper__step-main">
                                      <div class="pf-c-progress-stepper__step-title">
                                          ${currentPlan?.currentStage?.stageObj?.name}
                                      </div>
                                      <div class="pf-c-progress-stepper__step-description">
                                          ${currentPlan?.currentStage?.stageObj?.verboseName}
                                      </div>
                                  </div>
                              </li>`
                            : nothing}
                        ${currentPlan?.nextPlannedStage && !isCompleted
                            ? html`<li class="pf-c-progress-stepper__step pf-m-pending">
                                  <div class="pf-c-progress-stepper__step-connector">
                                      <span class="pf-c-progress-stepper__step-icon"></span>
                                  </div>
                                  <div class="pf-c-progress-stepper__step-main">
                                      <div class="pf-c-progress-stepper__step-title">
                                          ${currentPlan.nextPlannedStage.stageObj?.name}
                                      </div>
                                      <div class="pf-c-progress-stepper__step-description">
                                          ${currentPlan?.nextPlannedStage?.stageObj?.verboseName}
                                      </div>
                                  </div>
                              </li>`
                            : nothing}
                    </ol>
                </div>
            </fieldset>
        </div>`;
    }

    protected renderCurrentPlan({ currentPlan }: FlowInspection): TemplateResult {
        return html`<div class="pf-c-card">
            <fieldset>
                <legend class="pf-c-card__title">${msg("Current plan context")}</legend>
                <pre class="pf-c-card__body"><code>${stringify(
                    currentPlan?.planContext,
                )}</code></pre>
            </fieldset>
        </div>`;
    }

    protected renderSession({ currentPlan }: FlowInspection): TemplateResult {
        return html`<div class="pf-c-card">
            <fieldset>
                <legend class="pf-c-card__title">${msg("Session ID")}</legend>
                <div class="pf-c-card__body">
                    <code class="break"> ${currentPlan?.sessionId} </code>
                </div>
            </fieldset>
        </div>`;
    }

    protected render(): TemplateResult {
        if (this.error) {
            return this.renderAccessDenied();
        }
        if (!this.state) {
            this.advanceHandler();
            return html`<aside
                aria-label=${msg("Flow inspector loading")}
                class="pf-c-drawer__body pf-m-no-padding"
            >
                <div class="pf-c-notification-drawer">
                    ${this.renderHeader()}
                    <div class="pf-c-notification-drawer__body"></div>
                    <ak-empty-state loading> </ak-empty-state>
                </div>
            </aside>`;
        }

        return html`<aside
            aria-label=${msg("Flow inspector")}
            class="pf-c-drawer__body pf-m-no-padding"
        >
            <div class="pf-c-notification-drawer">
                ${this.renderHeader()}
                <div class="pf-c-notification-drawer__body">
                    <div class="pf-l-stack pf-m-gutter">
                        <div class="pf-l-stack__item">${this.renderNextStage(this.state)}</div>
                        <div class="pf-l-stack__item">${this.renderPlanHistory(this.state)}</div>
                        <div class="pf-l-stack__item">${this.renderCurrentPlan(this.state)}</div>
                        <div class="pf-l-stack__item">${this.renderSession(this.state)}</div>
                    </div>
                </div>
            </div>
        </aside>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-inspector": FlowInspector;
    }
}
