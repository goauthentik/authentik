import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { dateTimeLocal, first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { FlowsInstancesListDesignationEnum, Invitation, StagesApi } from "@goauthentik/api";

@customElement("ak-invitation-form")
export class InvitationForm extends ModelForm<Invitation, string> {
    loadInstance(pk: string): Promise<Invitation> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsRetrieve({
            inviteUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated invitation.");
        } else {
            return msg("Successfully created invitation.");
        }
    }

    async send(data: Invitation): Promise<Invitation> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUpdate({
                inviteUuid: this.instance.pk || "",
                invitationRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsCreate({
                invitationRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                ?slugMode=${true}
                label=${msg("Name")}
                ?required=${true}
                name="name"
            >
                <input
                    type="text"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                    data-ak-slug="true"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Expires")} ?required=${true} name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    value="${dateTimeLocal(first(this.instance?.expires, new Date()))}"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Flow")} ?required=${true} name="flow">
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
            <ak-form-element-horizontal label=${msg("Attributes")} name="fixedData">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.fixedData, {}))}"
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
                        ?checked=${first(this.instance?.singleUse, true)}
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
            </ak-form-element-horizontal>
        </form>`;
    }
}
