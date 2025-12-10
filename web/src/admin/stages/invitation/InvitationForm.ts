import "#admin/common/ak-flow-search/ak-flow-search";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { FlowsInstancesListDesignationEnum, Invitation, StagesApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-invitation-form")
export class InvitationForm extends ModelForm<Invitation, string> {
    loadInstance(pk: string): Promise<Invitation> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsRetrieve({
            inviteUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated invitation.")
            : msg("Successfully created invitation.");
    }

    async send(data: Invitation): Promise<Invitation> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUpdate({
                inviteUuid: this.instance.pk || "",
                invitationRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsCreate({
            invitationRequest: data,
        });
    }

    renderForm(): TemplateResult {
        const checkSlug = (ev: InputEvent) => {
            if (ev && ev.target && ev.target instanceof HTMLInputElement) {
                ev.target.value = (ev.target.value ?? "").replace(/[^a-z0-9-]/g, "");
            }
        };

        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    id="admin-stages-invitation-name"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                    @input=${(ev: InputEvent) => checkSlug(ev)}
                    data-ak-slug="true"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The name of an invitation must be a slug: only lower case letters, numbers, and the hyphen are permitted here.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Expires")} required name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    value="${dateTimeLocal(this.instance?.expires ?? new Date())}"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow")} name="flow">
                <ak-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                    .currentFlow=${this.instance?.flow}
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When selected, the invite will only be usable with the flow. By default the invite is accepted on all flows with invitation stages.",
                    )}
                </p>
            </ak-form-element-horizontal>
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
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="singleUse">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.singleUse ?? true}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Single use")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg("When enabled, the invitation will be deleted after usage.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-form": InvitationForm;
    }
}
