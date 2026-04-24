import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

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
import { customElement, property, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

interface EnrollmentFlow {
    slug: string;
    pk: string;
    name: string;
}

@customElement("ak-invitation-wizard-flow-step")
export class InvitationWizardFlowStep extends WizardPage {
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl, PFButton, PFAlert];

    @property({ type: String })
    public mode: "existing" | "create" = "existing";

    @state()
    enrollmentFlows: EnrollmentFlow[] = [];

    @state()
    loading = true;

    @state()
    selectedFlowSlug?: string;

    @state()
    selectedFlowPk?: string;

    @state()
    newFlowName = "Enrollment with invitation";

    @state()
    newFlowSlug = "enrollment-with-invitation";

    @state()
    newStageName = "invitation-stage";

    @state()
    newUserType: "external" | "internal" = "external";

    @state()
    continueFlowWithoutInvitation = true;

    activeCallback = async (): Promise<void> => {
        this.host.valid = false;

        if (this.mode === "create") {
            this.loading = false;
            this.validate();
            return;
        }

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

            if (this.enrollmentFlows.length > 0) {
                this.selectedFlowSlug = this.enrollmentFlows[0].slug;
                this.selectedFlowPk = this.enrollmentFlows[0].pk;
                this.host.valid = true;
            }
        } catch {
            this.enrollmentFlows = [];
        }

        this.loading = false;

        // If there's exactly one eligible flow, skip this step so the user goes
        // straight to the invitation details. Drop ourselves from the step list
        // so the back button from the next step doesn't bounce back here.
        if (this.mode === "existing" && this.enrollmentFlows.length === 1) {
            const currentSlot = this.slot;
            const advanced = await this.host.navigateNext();
            if (advanced) {
                this.host.steps = this.host.steps.filter((s) => s !== currentSlot);
            }
        }
    };

    validate(): void {
        if (this.mode === "existing") {
            this.host.valid = !!this.selectedFlowSlug;
        } else {
            this.host.valid =
                this.newFlowName.length > 0 &&
                this.newFlowSlug.length > 0 &&
                this.newStageName.length > 0;
        }
    }

    nextCallback = async (): Promise<boolean> => {
        const state = this.host.state as unknown as InvitationWizardState;

        state.flowMode = this.mode;

        if (this.mode === "existing") {
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
            state.newUserType = this.newUserType;
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
        this.selectedFlowSlug = undefined;
        this.selectedFlowPk = undefined;
        this.newFlowName = "Enrollment with invitation";
        this.newFlowSlug = "enrollment-with-invitation";
        this.newStageName = "invitation-stage";
        this.newUserType = "external";
        this.continueFlowWithoutInvitation = true;
    }

    slugify(value: string): string {
        return value
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
    }

    renderExistingFlowSelector(): TemplateResult {
        if (this.enrollmentFlows.length === 0) {
            return html`
                <div class="pf-c-alert pf-m-warning pf-m-inline">
                    <div class="pf-c-alert__icon">
                        <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                    </div>
                    <h4 class="pf-c-alert__title">
                        ${msg("No enrollment flows with invitation stages found")}
                    </h4>
                    <div class="pf-c-alert__description">
                        <p>
                            ${msg(
                                "You can create a new enrollment flow and invitation stage right here, or cancel and bind an invitation stage to an existing flow manually.",
                            )}
                        </p>
                        <button
                            type="button"
                            class="pf-c-button pf-m-primary"
                            @click=${() => {
                                this.mode = "create";
                                this.validate();
                            }}
                        >
                            ${msg("Create a new enrollment flow")}
                        </button>
                    </div>
                </div>
            `;
        }

        return html`
            <ak-form-element-horizontal label=${msg("Enrollment flow")} required>
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<EnrollmentFlow[]> => {
                        if (!query) return this.enrollmentFlows;
                        const needle = query.toLowerCase();
                        return this.enrollmentFlows.filter(
                            (flow) =>
                                flow.name.toLowerCase().includes(needle) ||
                                flow.slug.toLowerCase().includes(needle),
                        );
                    }}
                    .renderElement=${(flow: EnrollmentFlow): string => flow.name}
                    .renderDescription=${(flow: EnrollmentFlow): TemplateResult =>
                        html`${flow.slug}`}
                    .value=${(flow: EnrollmentFlow | undefined): string | undefined => flow?.pk}
                    .selected=${(flow: EnrollmentFlow): boolean => flow.pk === this.selectedFlowPk}
                    @ak-change=${(ev: CustomEvent<{ value: EnrollmentFlow | null }>) => {
                        const flow = ev.detail.value;
                        this.selectedFlowSlug = flow?.slug;
                        this.selectedFlowPk = flow?.pk;
                        this.validate();
                    }}
                    style="display: block; width: 100%;"
                ></ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Only enrollment flows that have an invitation stage bound to them are listed here.",
                    )}
                </p>
            </ak-form-element-horizontal>
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
            <ak-radio-input
                label=${msg("User type")}
                .value=${this.newUserType}
                .options=${[
                    {
                        label: msg("External"),
                        value: "external",
                        description: html`${msg(
                            "Enrolled users are created as external (e.g. customers, guests). New users will be placed under users/external.",
                        )}`,
                    },
                    {
                        label: msg("Internal"),
                        value: "internal",
                        description: html`${msg(
                            "Enrolled users are created as internal (e.g. employees). New users will be placed under users/internal.",
                        )}`,
                    },
                ]}
                @input=${(ev: CustomEvent<{ value: "external" | "internal" }>) => {
                    this.newUserType = ev.detail.value;
                }}
            ></ak-radio-input>
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
            ${this.mode === "existing"
                ? this.renderExistingFlowSelector()
                : this.renderCreateForm()}
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-flow-step": InvitationWizardFlowStep;
    }
}
