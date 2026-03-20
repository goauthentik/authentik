import "#components/ak-switch-input";
import "#elements/forms/HorizontalFormElement";

import type { InvitationWizardState } from "./types";

import { DEFAULT_CONFIG } from "#common/api/config";

import { WizardPage } from "#elements/wizard/WizardPage";

import {
    FlowDesignationEnum,
    type FlowSet,
    type InvitationStage,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

interface EnrollmentFlow {
    slug: string;
    pk: string;
    name: string;
}

@customElement("ak-invitation-wizard-flow-step")
export class InvitationWizardFlowStep extends WizardPage {
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl, PFButton, PFRadio, PFAlert];

    label = msg("Enrollment Flow");

    @state()
    enrollmentFlows: EnrollmentFlow[] = [];

    @state()
    loading = true;

    @state()
    flowMode: "existing" | "create" = "existing";

    @state()
    selectedFlowSlug?: string;

    @state()
    selectedFlowPk?: string;

    @state()
    newFlowName = "";

    @state()
    newFlowSlug = "";

    @state()
    newStageName = "";

    @state()
    continueFlowWithoutInvitation = true;

    activeCallback = async (): Promise<void> => {
        this.host.isValid = false;
        this.loading = true;

        try {
            const stages = await new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesList({
                noFlows: false,
            });

            const flowMap = new Map<string, EnrollmentFlow>();

            stages.results.forEach((stage: InvitationStage) => {
                (stage.flowSet || [])
                    .filter((flow: FlowSet) => flow.designation === FlowDesignationEnum.Enrollment)
                    .forEach((flow: FlowSet) => {
                        if (!flowMap.has(flow.slug)) {
                            flowMap.set(flow.slug, {
                                slug: flow.slug,
                                pk: flow.pk,
                                name: flow.name,
                            });
                        }
                    });
            });

            this.enrollmentFlows = Array.from(flowMap.values());

            if (this.enrollmentFlows.length === 0) {
                this.flowMode = "create";
                this.newFlowName = "Enrollment with invitation";
                this.newFlowSlug = "enrollment-with-invitation";
                this.newStageName = "invitation-stage";
                this.validate();
            } else {
                this.flowMode = "existing";
                this.selectedFlowSlug = this.enrollmentFlows[0].slug;
                this.selectedFlowPk = this.enrollmentFlows[0].pk;
                this.host.isValid = true;
            }
        } catch {
            this.enrollmentFlows = [];
            this.flowMode = "create";
        }

        this.loading = false;
    };

    validate(): void {
        if (this.flowMode === "existing") {
            this.host.isValid = !!this.selectedFlowSlug;
        } else {
            this.host.isValid =
                this.newFlowName.length > 0 &&
                this.newFlowSlug.length > 0 &&
                this.newStageName.length > 0;
        }
    }

    nextCallback = async (): Promise<boolean> => {
        const state = this.host.state as InvitationWizardState;

        state.flowMode = this.flowMode;

        if (this.flowMode === "existing") {
            if (!this.selectedFlowSlug) return false;
            state.selectedFlowSlug = this.selectedFlowSlug;
            state.selectedFlowPk = this.selectedFlowPk;
            state.needsFlow = false;
            state.needsStage = false;
            state.needsBinding = false;
        } else {
            if (!this.newFlowName || !this.newFlowSlug || !this.newStageName) return false;
            state.newFlowName = this.newFlowName;
            state.newFlowSlug = this.newFlowSlug;
            state.newStageName = this.newStageName;
            state.continueFlowWithoutInvitation = this.continueFlowWithoutInvitation;
            state.needsFlow = true;
            state.needsStage = true;
            state.needsBinding = true;
        }

        return true;
    };

    override reset(): void {
        this.enrollmentFlows = [];
        this.loading = true;
        this.flowMode = "existing";
        this.selectedFlowSlug = undefined;
        this.selectedFlowPk = undefined;
        this.newFlowName = "";
        this.newFlowSlug = "";
        this.newStageName = "";
        this.continueFlowWithoutInvitation = true;
    }

    slugify(value: string): string {
        return value
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
    }

    renderExistingFlowSelector(): TemplateResult {
        return html`
            <div class="pf-c-form__group">
                ${this.enrollmentFlows.map(
                    (flow) => html`
                        <div class="pf-c-radio">
                            <input
                                class="pf-c-radio__input"
                                type="radio"
                                name="existing-flow"
                                id="flow-${flow.slug}"
                                ?checked=${this.selectedFlowSlug === flow.slug}
                                @change=${() => {
                                    this.selectedFlowSlug = flow.slug;
                                    this.selectedFlowPk = flow.pk;
                                    this.validate();
                                }}
                            />
                            <label class="pf-c-radio__label" for="flow-${flow.slug}">
                                ${flow.name}
                            </label>
                            <span class="pf-c-radio__description">${flow.slug}</span>
                        </div>
                    `,
                )}
            </div>
        `;
    }

    renderCreateForm(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Flow name")} required>
                <input
                    type="text"
                    class="pf-c-form-control"
                    required
                    .value=${this.newFlowName}
                    @input=${(ev: InputEvent) => {
                        const target = ev.target as HTMLInputElement;
                        this.newFlowName = target.value;
                        this.newFlowSlug = this.slugify(target.value);
                        this.validate();
                    }}
                />
                <p class="pf-c-form__helper-text">${msg("Name for the new enrollment flow.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow slug")} required>
                <input
                    type="text"
                    class="pf-c-form-control"
                    required
                    .value=${this.newFlowSlug}
                    @input=${(ev: InputEvent) => {
                        const target = ev.target as HTMLInputElement;
                        this.newFlowSlug = target.value.replace(/[^a-z0-9-]/g, "");
                        this.validate();
                    }}
                />
                <p class="pf-c-form__helper-text">${msg("Visible in the URL.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Invitation stage name")} required>
                <input
                    type="text"
                    class="pf-c-form-control"
                    required
                    .value=${this.newStageName}
                    @input=${(ev: InputEvent) => {
                        this.newStageName = (ev.target as HTMLInputElement).value;
                        this.validate();
                    }}
                />
                <p class="pf-c-form__helper-text">${msg("Name for the new invitation stage.")}</p>
            </ak-form-element-horizontal>
            <ak-switch-input
                label=${msg("Continue flow without invitation")}
                ?checked=${this.continueFlowWithoutInvitation}
                @change=${(ev: Event) => {
                    this.continueFlowWithoutInvitation = (ev.target as HTMLInputElement).checked;
                }}
                help=${msg(
                    "If enabled, the stage will jump to the next stage when no invitation is given. If disabled, the flow will be cancelled without a valid invitation.",
                )}
            ></ak-switch-input>
        `;
    }

    render(): TemplateResult {
        if (this.loading) {
            return html`<div class="pf-c-form">
                <p>${msg("Loading...")}</p>
            </div>`;
        }

        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.enrollmentFlows.length === 0
                ? html`
                      <div class="pf-c-alert pf-m-info pf-m-inline">
                          <div class="pf-c-alert__icon">
                              <i class="fas fa-info-circle" aria-hidden="true"></i>
                          </div>
                          <h4 class="pf-c-alert__title">
                              ${msg("No enrollment flows with invitation stages found")}
                          </h4>
                          <div class="pf-c-alert__description">
                              <p>
                                  ${msg(
                                      "A new enrollment flow and invitation stage will be created for you.",
                                  )}
                              </p>
                          </div>
                      </div>
                      ${this.renderCreateForm()}
                  `
                : html`
                      <div class="pf-c-form__group">
                          <div class="pf-c-radio">
                              <input
                                  class="pf-c-radio__input"
                                  type="radio"
                                  name="flow-mode"
                                  id="flow-mode-existing"
                                  ?checked=${this.flowMode === "existing"}
                                  @change=${() => {
                                      this.flowMode = "existing";
                                      if (this.enrollmentFlows.length > 0) {
                                          this.selectedFlowSlug = this.enrollmentFlows[0].slug;
                                          this.selectedFlowPk = this.enrollmentFlows[0].pk;
                                      }
                                      this.validate();
                                  }}
                              />
                              <label class="pf-c-radio__label" for="flow-mode-existing">
                                  ${msg("Use existing enrollment flow")}
                              </label>
                          </div>
                          <div class="pf-c-radio">
                              <input
                                  class="pf-c-radio__input"
                                  type="radio"
                                  name="flow-mode"
                                  id="flow-mode-create"
                                  ?checked=${this.flowMode === "create"}
                                  @change=${() => {
                                      this.flowMode = "create";
                                      this.newFlowName = "Enrollment with invitation";
                                      this.newFlowSlug = "enrollment-with-invitation";
                                      this.newStageName = "invitation-stage";
                                      this.validate();
                                  }}
                              />
                              <label class="pf-c-radio__label" for="flow-mode-create">
                                  ${msg("Create new enrollment flow")}
                              </label>
                          </div>
                      </div>

                      ${this.flowMode === "existing"
                          ? this.renderExistingFlowSelector()
                          : this.renderCreateForm()}
                  `}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-flow-step": InvitationWizardFlowStep;
    }
}
