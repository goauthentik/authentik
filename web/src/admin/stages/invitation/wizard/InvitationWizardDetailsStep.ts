import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import type { InvitationWizardState } from "./types";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import type { WizardAction } from "#elements/wizard/Wizard";
import { WizardPage } from "#elements/wizard/WizardPage";

import { FlowDesignationEnum, FlowsApi, StagesApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-invitation-wizard-details-step")
export class InvitationWizardDetailsStep extends WizardPage {
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl];

    label = msg("Invitation Details");

    @state()
    invitationName = "";

    @state()
    invitationExpires: string = dateTimeLocal(new Date(Date.now() + 48 * 60 * 60 * 1000));

    @state()
    fixedDataRaw = "{}";

    @state()
    singleUse = true;

    activeCallback = async (): Promise<void> => {
        this.host.isValid = this.invitationName.length > 0;
    };

    validate(): void {
        let validYaml = true;
        try {
            YAML.parse(this.fixedDataRaw);
        } catch {
            validYaml = false;
        }
        this.host.isValid =
            this.invitationName.length > 0 && this.invitationExpires.length > 0 && validYaml;
    }

    nextCallback = async (): Promise<boolean> => {
        if (!this.invitationName) return false;

        let fixedData: Record<string, unknown> = {};
        try {
            fixedData = YAML.parse(this.fixedDataRaw) || {};
        } catch {
            return false;
        }

        const wizardState = this.host.state as InvitationWizardState;
        wizardState.invitationName = this.invitationName;
        wizardState.invitationExpires = this.invitationExpires;
        wizardState.invitationFixedData = fixedData;
        wizardState.invitationSingleUse = this.singleUse;

        const actions: WizardAction[] = [];

        if (wizardState.needsStage) {
            actions.push({
                displayName: msg("Create invitation stage"),
                run: async () => {
                    const stage = await new StagesApi(DEFAULT_CONFIG).stagesInvitationStagesCreate({
                        invitationStageRequest: {
                            name: wizardState.newStageName!,
                            continueFlowWithoutInvitation:
                                wizardState.continueFlowWithoutInvitation,
                        },
                    });
                    wizardState.createdStagePk = stage.pk;
                    return true;
                },
            });
        }

        if (wizardState.needsFlow) {
            actions.push({
                displayName: msg("Create enrollment flow"),
                run: async () => {
                    const flow = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesCreate({
                        flowRequest: {
                            name: wizardState.newFlowName!,
                            slug: wizardState.newFlowSlug!,
                            title: wizardState.newFlowName!,
                            designation: FlowDesignationEnum.Enrollment,
                        },
                    });
                    wizardState.createdFlowPk = flow.pk;
                    wizardState.createdFlowSlug = flow.slug;
                    return true;
                },
            });
        }

        if (wizardState.needsBinding) {
            actions.push({
                displayName: msg("Bind stage to flow"),
                run: async () => {
                    const target = wizardState.createdFlowPk!;
                    const stage = wizardState.createdStagePk!;
                    await new FlowsApi(DEFAULT_CONFIG).flowsBindingsCreate({
                        flowStageBindingRequest: {
                            target,
                            stage,
                            order: 0,
                        },
                    });
                    return true;
                },
            });
        }

        actions.push({
            displayName: msg("Create invitation"),
            run: async () => {
                const flowPk = wizardState.createdFlowPk || wizardState.selectedFlowPk || undefined;

                const invitation = await new StagesApi(
                    DEFAULT_CONFIG,
                ).stagesInvitationInvitationsCreate({
                    invitationRequest: {
                        name: wizardState.invitationName!,
                        expires: wizardState.invitationExpires
                            ? new Date(wizardState.invitationExpires)
                            : undefined,
                        fixedData: wizardState.invitationFixedData,
                        singleUse: wizardState.invitationSingleUse,
                        flow: flowPk || null,
                    },
                });
                wizardState.createdInvitationPk = invitation.pk;
                return true;
            },
        });

        this.host.actions = actions;
        return true;
    };

    override reset(): void {
        this.invitationName = "";
        this.invitationExpires = dateTimeLocal(new Date(Date.now() + 48 * 60 * 60 * 1000));
        this.fixedDataRaw = "{}";
        this.singleUse = true;
    }

    render(): TemplateResult {
        const wizardState = this.host.state as InvitationWizardState;
        const flowDisplay =
            wizardState.flowMode === "existing"
                ? wizardState.selectedFlowSlug
                : wizardState.newFlowSlug;

        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} required>
                <input
                    type="text"
                    class="pf-c-form-control"
                    required
                    .value=${this.invitationName}
                    @input=${(ev: InputEvent) => {
                        const target = ev.target as HTMLInputElement;
                        this.invitationName = target.value.replace(/[^a-z0-9-]/g, "");
                        target.value = this.invitationName;
                        this.validate();
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The name of an invitation must be a slug: only lower case letters, numbers, and the hyphen are permitted here.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Expires")} required>
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    .value=${this.invitationExpires}
                    @input=${(ev: InputEvent) => {
                        this.invitationExpires = (ev.target as HTMLInputElement).value;
                        this.validate();
                    }}
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow")}>
                <input
                    type="text"
                    class="pf-c-form-control"
                    readonly
                    disabled
                    .value=${flowDisplay || ""}
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The flow selected in the previous step. The invitation will be bound to this flow.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Custom attributes")}>
                <ak-codemirror
                    mode="yaml"
                    .value=${this.fixedDataRaw}
                    @change=${(ev: CustomEvent) => {
                        this.fixedDataRaw = ev.detail.value;
                        this.validate();
                    }}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                label=${msg("Single use")}
                ?checked=${this.singleUse}
                @change=${(ev: Event) => {
                    this.singleUse = (ev.target as HTMLInputElement).checked;
                }}
                help=${msg("When enabled, the invitation will be deleted after usage.")}
            ></ak-switch-input>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-details-step": InvitationWizardDetailsStep;
    }
}
