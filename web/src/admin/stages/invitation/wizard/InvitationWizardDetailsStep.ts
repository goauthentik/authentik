import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import type { InvitationWizardState } from "./types";

import { aki } from "#common/api/client";
import {
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { dateTimeLocal } from "#common/temporal";

import { serializeForm } from "#elements/forms/serialization";
import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { WizardPage } from "#elements/wizard/WizardPage";

import { FlowsApi, ManagedApi, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

const MINIMAL_BLUEPRINT_PATH = "example/flows-invitation-enrollment-minimal.yaml";

/**
 * Serialized payload of the details form.
 */
interface DetailsFormData {
    name: string;
    expires?: Date;
    fixedData?: Record<string, unknown> | null;
    singleUse: boolean;
}

@customElement("ak-invitation-wizard-details-step")
export class InvitationWizardDetailsStep extends WizardPage<InvitationWizardState> {
    static styles: CSSResult[] = [PFForm, PFFormControl];

    #defaultExpires = dateTimeLocal(new Date(Date.now() + 48 * 60 * 60 * 1000));

    protected get form(): HTMLFormElement | null {
        return this.renderRoot.querySelector("form");
    }

    //#region Validation

    protected syncValidity = (): void => {
        this.host.valid = this.form?.checkValidity() ?? false;
    };

    public override activeCallback = async (): Promise<void> => {
        this.syncValidity();
    };

    //#endregion

    //#region API orchestration

    protected async reportStepError(step: string, error: unknown): Promise<false> {
        const parsed = await parseAPIResponseError(error);
        const fieldErrors = pluckFallbackFieldErrors(parsed);
        const detail = fieldErrors.length ? fieldErrors.join(" ") : pluckErrorDetail(parsed);

        showMessage({
            level: MessageLevel.error,
            message: msg(str`${step} failed`),
            description: detail,
        });

        this.logger.error("Invitation wizard step failed", { step, error });

        return false;
    }

    /**
     * Import the minimal enrollment-flow blueprint and record the created flow on the wizard state.
     */
    async #importEnrollmentFlow(state: InvitationWizardState): Promise<boolean> {
        const label = msg("Importing enrollment flow blueprint");

        return aki(ManagedApi)
            .managedBlueprintsImportCreate({
                path: MINIMAL_BLUEPRINT_PATH,
                context: JSON.stringify({
                    flow_name: state.newFlowName,
                    flow_slug: state.newFlowSlug,
                    stage_name: state.newStageName,
                    continue_flow_without_invitation: state.continueFlowWithoutInvitation,
                    user_type: state.newUserType,
                }),
            })
            .then(async (result) => {
                if (!result.success) {
                    const logs = (result.logs || [])
                        .map((entry) => entry.event)
                        .filter(Boolean)
                        .join("\n");

                    return this.reportStepError(
                        label,
                        new Error(logs || msg("Blueprint validation failed")),
                    );
                }

                const slug = state.newFlowSlug!;

                const { results } = await aki(FlowsApi).flowsInstancesList({ slug });
                const createdFlow = results[0];

                if (!createdFlow) {
                    return this.reportStepError(
                        label,
                        new Error(msg(str`Flow with slug "${slug}" not found after import`)),
                    );
                }

                Object.assign(state, {
                    createdFlowPk: createdFlow.pk,
                    createdFlowSlug: createdFlow.slug,
                    needsFlow: false,
                    needsStage: false,
                    needsBinding: false,
                } satisfies Partial<InvitationWizardState>);

                return true;
            })
            .catch((error) => {
                return this.reportStepError(label, error);
            });
    }

    /**
     * Create the invitation, binding it to the created/selected flow, and record it on the state.
     */
    async #createInvitation(state: InvitationWizardState, data: DetailsFormData): Promise<boolean> {
        try {
            const invitation = await aki(StagesApi).stagesInvitationInvitationsCreate({
                invitationRequest: {
                    name: data.name,
                    expires: data.expires,
                    fixedData: data.fixedData ?? {},
                    singleUse: data.singleUse,
                    flow: state.createdFlowPk || state.selectedFlowPk || null,
                },
            });

            state.createdInvitationPk = invitation.pk;
            state.createdInvitation = invitation;

            return true;
        } catch (error) {
            return this.reportStepError(msg("Creating invitation"), error);
        }
    }

    public override nextCallback = async (): Promise<boolean> => {
        const { form } = this;

        if (!form || !form.reportValidity()) return false;

        const { state } = this.host;

        // Already created on a previous attempt (e.g. the user stepped back and forward again).
        if (state.createdInvitationPk) return true;

        if (state.needsFlow && !(await this.#importEnrollmentFlow(state))) {
            return false;
        }

        const data = serializeForm<DetailsFormData>(
            form.querySelectorAll("ak-form-element-horizontal"),
        );

        return this.#createInvitation(state, data);
    };

    //#endregion

    //#region Rendering

    protected override render(): SlottedTemplateResult {
        const { state } = this.host;

        const flowDisplay =
            (state.flowMode === "existing" ? state.selectedFlowSlug : state.newFlowSlug) ??
            msg("No flow selected");

        return html`<form class="pf-c-form pf-m-horizontal" @input=${this.syncValidity}>
            <ak-slug-input
                name="name"
                label=${msg("Invitation Name")}
                autofocus
                required
                help=${msg(
                    "The name of an invitation must be a slug: only lower case letters, numbers, and the hyphen are permitted here.",
                )}
            ></ak-slug-input>
            <ak-form-element-horizontal label=${msg("Expires")} required name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    value=${this.#defaultExpires}
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow")}>
                <input
                    type="text"
                    class="pf-c-form-control"
                    readonly
                    disabled
                    .value=${flowDisplay}
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The flow selected in the previous step. The invitation will be bound to this flow.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Custom attributes")} name="fixedData">
                <ak-codemirror mode="yaml" value="{}"></ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="singleUse"
                label=${msg("Single use")}
                checked
                help=${msg("When enabled, the invitation will be deleted after usage.")}
            ></ak-switch-input>
        </form>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-details-step": InvitationWizardDetailsStep;
    }
}
