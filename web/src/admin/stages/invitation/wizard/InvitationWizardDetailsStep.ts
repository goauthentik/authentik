import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import type { InvitationWizardState } from "./types";

import { DEFAULT_CONFIG } from "#common/api/config";
import {
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { dateTimeLocal } from "#common/temporal";

import { showMessage } from "#elements/messages/MessageContainer";
import { WizardPage } from "#elements/wizard/WizardPage";

import { FlowsApi, ManagedApi, StagesApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

const MINIMAL_BLUEPRINT_PATH = "example/flows-invitation-enrollment-minimal.yaml";

@customElement("ak-invitation-wizard-details-step")
export class InvitationWizardDetailsStep extends WizardPage {
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl];

    @state()
    invitationName = "";

    @state()
    invitationExpires: string = dateTimeLocal(new Date(Date.now() + 48 * 60 * 60 * 1000));

    @state()
    fixedDataRaw = "{}";

    @state()
    singleUse = true;

    activeCallback = async (): Promise<void> => {
        this.host.valid = this.invitationName.length > 0;
    };

    async #fail(step: string, err: unknown): Promise<false> {
        const parsed = await parseAPIResponseError(err);
        const fieldErrors = pluckFallbackFieldErrors(parsed);
        const detail = fieldErrors.length > 0 ? fieldErrors.join(" ") : pluckErrorDetail(parsed);
        showMessage({
            level: MessageLevel.error,
            message: msg(str`${step} failed`),
            description: detail,
        });
        this.logger.error("Invitation wizard step failed", { step, error: err });
        return false;
    }

    validate(): void {
        let validYaml = true;
        try {
            YAML.parse(this.fixedDataRaw);
        } catch {
            validYaml = false;
        }
        this.host.valid =
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

        const wizardState = this.host.state as unknown as InvitationWizardState;

        if (wizardState.createdInvitationPk) {
            return true;
        }

        wizardState.invitationName = this.invitationName;
        wizardState.invitationExpires = this.invitationExpires;
        wizardState.invitationFixedData = fixedData;
        wizardState.invitationSingleUse = this.singleUse;

        if (wizardState.needsFlow) {
            try {
                const result = await new ManagedApi(DEFAULT_CONFIG).managedBlueprintsImportCreate({
                    path: MINIMAL_BLUEPRINT_PATH,
                    context: JSON.stringify({
                        flow_name: wizardState.newFlowName,
                        flow_slug: wizardState.newFlowSlug,
                        stage_name: wizardState.newStageName,
                        continue_flow_without_invitation: wizardState.continueFlowWithoutInvitation,
                        user_type: wizardState.newUserType,
                    }),
                });
                if (!result.success) {
                    const logs = (result.logs || [])
                        .map((l) => l.event)
                        .filter((m) => !!m)
                        .join("\n");
                    return this.#fail(
                        msg("Importing enrollment flow blueprint"),
                        new Error(logs || msg("Blueprint validation failed")),
                    );
                }

                const slugToLookup = wizardState.newFlowSlug!;
                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                    slug: slugToLookup,
                });
                const createdFlow = flows.results[0];
                if (!createdFlow) {
                    return this.#fail(
                        msg("Importing enrollment flow blueprint"),
                        new Error(
                            msg(str`Flow with slug "${slugToLookup}" not found after import`),
                        ),
                    );
                }
                wizardState.createdFlowPk = createdFlow.pk;
                wizardState.createdFlowSlug = createdFlow.slug;
                wizardState.needsFlow = false;
                wizardState.needsStage = false;
                wizardState.needsBinding = false;
            } catch (err) {
                return this.#fail(msg("Importing enrollment flow blueprint"), err);
            }
        }

        try {
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
            wizardState.createdInvitation = invitation;
        } catch (err) {
            return this.#fail(msg("Creating invitation"), err);
        }

        return true;
    };

    override reset(): void {
        this.invitationName = "";
        this.invitationExpires = dateTimeLocal(new Date(Date.now() + 48 * 60 * 60 * 1000));
        this.fixedDataRaw = "{}";
        this.singleUse = true;
    }

    render(): TemplateResult {
        const wizardState = this.host.state as unknown as InvitationWizardState;
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
