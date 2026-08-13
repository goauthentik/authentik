import "#admin/common/ak-flow-search/ak-flow-search";
import "#admin/stages/invitation/InvitationListLink";
import "#components/ak-switch-input";
import "#components/ak-slug-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { dateTimeLocal } from "#common/temporal";

import { renderDialog, renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import { ModelForm } from "#elements/forms/ModelForm";

import type { AkFlowSearch } from "#admin/common/ak-flow-search/ak-flow-search";
import { InvitationEnrollmentFlowForm } from "#admin/stages/invitation/InvitationEnrollmentFlowForm";

import { Flow, FlowDesignationEnum, Invitation, StagesApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

@customElement("ak-invitation-form")
export class InvitationForm extends ModelForm<Invitation, string> {
    public static override verboseName = msg("Invitation");
    public static override verboseNamePlural = msg("Invitations");

    protected flowSearchRef = createRef<AkFlowSearch<Flow>>();

    protected endpoints = {
        load: (inviteUuid: string) =>
            aki(StagesApi).stagesInvitationInvitationsRetrieve({ inviteUuid }),
        create: (invitationRequest: Invitation) =>
            aki(StagesApi).stagesInvitationInvitationsCreate({ invitationRequest }),
        update: (inviteUuid: string, invitationRequest: Invitation) =>
            aki(StagesApi).stagesInvitationInvitationsUpdate({ inviteUuid, invitationRequest }),
    };

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated invitation.")
            : msg("Successfully created invitation.");
    }

    /**
     * The native `required` attribute inside the flow search cannot participate in the
     * outer form's validity across the shadow boundary, and the API accepts a null
     * flow — so enforce the selection here. An invitation without a flow produces a
     * link that cannot be used.
     */
    public override reportValidity(): boolean {
        const valid = super.reportValidity();

        const flowSearch = this.renderRoot.querySelector("ak-flow-search");

        if (!flowSearch) return valid;

        if (!flowSearch.value) {
            flowSearch.errorMessages = [msg("Select an enrollment flow.")];
            return false;
        }

        flowSearch.errorMessages = [];

        return valid;
    }

    /**
     * Open a stacked modal to create a new enrollment flow with an invitation
     * stage bound to it, without losing the current form state.
     *
     * Once created, the flow search refreshes its options and selects the new flow.
     */
    openNewEnrollmentFlowModal = (invocationEvent?: Event) => {
        invocationEvent?.stopPropagation();

        const enrollmentFlowForm = new InvitationEnrollmentFlowForm();

        let createdFlow: Flow | null = null;

        enrollmentFlowForm.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
            createdFlow = (event as AKFormSubmittedEvent<Flow>).response;
        });

        return renderModal(enrollmentFlowForm, {
            invokerElement:
                invocationEvent?.target instanceof HTMLElement ? invocationEvent.target : this,
            size: PFSize.Medium,
            onDispose: (disposeEvent) => {
                const { target } = disposeEvent || {};

                if (!(target instanceof HTMLDialogElement) || target.returnValue !== "submitted") {
                    return;
                }

                const flowSearch = this.flowSearchRef.value;

                if (!flowSearch) {
                    this.logger.error(
                        "Failed to refresh flow search after creating new enrollment flow. No flow search found.",
                    );

                    return;
                }

                // Refresh the flow search and select the newly created flow.
                if (!createdFlow) {
                    this.logger.error(
                        "Enrollment flow form closed as submitted, but no created flow was captured.",
                    );

                    return;
                }

                flowSearch.errorMessages = [];
                flowSearch.refresh(createdFlow);
            },
        });
    };

    /**
     * Close the confirmation modal via its footer button.
     */
    #confirmationCloseListener = (event: Event) => {
        const target = event.target as HTMLElement;

        target.closest("ak-modal")?.close("close");
    };

    protected override send(data: Invitation): Promise<unknown> {
        const creating = this.instancePk === null;

        return super.send(data).then((response) => {
            if (creating) {
                // Show the freshly created invitation's link so the user can copy
                // it or send it via email right away.
                renderDialog(
                    html`<ak-modal headline=${msg("Invitation Details")} size=${PFSize.Medium}>
                        <ak-stage-invitation-list-link
                            .invitation=${response as Invitation}
                        ></ak-stage-invitation-list-link>
                        <button
                            slot="actions"
                            type="button"
                            class="pf-c-button pf-m-primary"
                            @click=${this.#confirmationCloseListener}
                        >
                            ${msg("Close")}
                        </button>
                    </ak-modal>`,
                );
            }

            return response;
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-slug-input
                label=${msg("Invitation Name")}
                placeholder=${msg("e.g. my-invite")}
                required
                name="name"
                value="${this.instance?.name || ""}"
                autofocus
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
                    value="${dateTimeLocal(
                        this.instance?.expires ?? new Date(Date.now() + 48 * 60 * 60 * 1000),
                    )}"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow")} required name="flow">
                <ak-flow-search
                    ${ref(this.flowSearchRef)}
                    required
                    flowType=${FlowDesignationEnum.Enrollment}
                    .currentFlow=${this.instance?.flow}
                    action-label=${msg("Create a new enrollment flow with invitation stage...")}
                    @ak-search-select-action=${this.openNewEnrollmentFlowModal}
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The enrollment flow the invitation link will use. The flow should have an invitation stage bound to it for the invitation to be accepted.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="singleUse"
                label=${msg("Single use")}
                ?checked=${this.instance?.singleUse ?? true}
                help=${msg("When enabled, the invitation will be deleted after usage.")}
            ></ak-switch-input>
            <ak-form-element-horizontal label=${msg("Custom attributes")} name="fixedData">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(this.instance?.fixedData ?? {})}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-form": InvitationForm;
    }
}
