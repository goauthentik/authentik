import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";

import { aki } from "#common/api/client";

import { Form } from "#elements/forms/Form";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { Flow, FlowsApi, ManagedApi, UserTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

const MINIMAL_BLUEPRINT_PATH = "example/flows-invitation-enrollment-minimal.yaml";

/**
 * Serialized payload of {@linkcode InvitationEnrollmentFlowForm}.
 */
export interface InvitationEnrollmentFlowFormData {
    flowName: string;
    slug: string;
    stageName: string;
    userType?: "external" | "internal";
    continueFlowWithoutInvitation: boolean;
}

/**
 * A form which imports the minimal enrollment-flow blueprint, creating an
 * enrollment flow with an invitation stage bound to it.
 *
 * Resolves with the created {@linkcode Flow} on success.
 */
@customElement("ak-invitation-enrollment-flow-form")
export class InvitationEnrollmentFlowForm extends Form<InvitationEnrollmentFlowFormData> {
    public static override verboseName = msg("Enrollment Flow");
    public static override verboseNamePlural = msg("Enrollment Flows");

    public override getSuccessMessage(): string {
        return msg("Successfully created enrollment flow with invitation stage.");
    }

    protected override async send(data: InvitationEnrollmentFlowFormData): Promise<Flow> {
        const result = await aki(ManagedApi).managedBlueprintsImportCreate({
            path: MINIMAL_BLUEPRINT_PATH,
            context: JSON.stringify({
                flow_name: data.flowName,
                flow_slug: data.slug,
                stage_name: data.stageName,
                continue_flow_without_invitation: data.continueFlowWithoutInvitation ?? true,
                user_type: data.userType ?? "external",
            }),
        });

        if (!result.success) {
            const logs = (result.logs || [])
                .map((entry) => entry.event)
                .filter(Boolean)
                .join("\n");

            throw new Error(logs || msg("Blueprint validation failed"));
        }

        const { results } = await aki(FlowsApi).flowsInstancesList({ slug: data.slug });
        const createdFlow = results[0];

        if (!createdFlow) {
            throw new Error(msg(str`Flow with slug "${data.slug}" not found after import`));
        }

        return createdFlow;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                value="Enrollment with invitation"
                name="flowName"
                label=${msg("Flow Name")}
                required
                placeholder=${msg("Type a name for the new enrollment flow...")}
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                label=${msg("Flow Slug")}
                value="enrollment-with-invitation"
                required
                help=${msg("Internal flow name used in URLs.")}
                placeholder=${msg("e.g. my-enrollment-flow")}
                input-hint="code"
            ></ak-slug-input>
            <ak-text-input
                name="stageName"
                label=${msg("Invitation Stage Name")}
                value="invitation-stage"
                required
                input-hint="code"
                placeholder=${msg("Type a name for the stage...")}
            ></ak-text-input>
            <ak-radio-input
                label=${msg("User type")}
                name="userType"
                .options=${[
                    {
                        label: msg("External"),
                        default: true,
                        value: "external",
                        description: msg(
                            "Enrolled users are created as external (e.g. customers, guests). New users will be placed under users/external.",
                        ),
                    },
                    {
                        label: msg("Internal"),
                        value: "internal",
                        description: msg(
                            "Enrolled users are created as internal (e.g. employees). New users will be placed under users/internal.",
                        ),
                    },
                ] satisfies RadioOption<UserTypeEnum>[]}
            ></ak-radio-input>
            <ak-switch-input
                label=${msg("Continue flow without invitation")}
                checked
                name="continueFlowWithoutInvitation"
                help=${msg(
                    "If enabled, the stage will jump to the next stage when no invitation is given. If disabled, the flow will be cancelled without a valid invitation.",
                )}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-enrollment-flow-form": InvitationEnrollmentFlowForm;
    }
}
