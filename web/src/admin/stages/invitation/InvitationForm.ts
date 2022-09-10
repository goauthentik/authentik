import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/CodeMirror";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/web/elements/forms/ModelForm";
import { dateTimeLocal, first } from "@goauthentik/web/utils";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { Invitation, StagesApi } from "@goauthentik/api";

@customElement("ak-invitation-form")
export class InvitationForm extends ModelForm<Invitation, string> {
    loadInstance(pk: string): Promise<Invitation> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsRetrieve({
            inviteUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated invitation.`;
        } else {
            return t`Successfully created invitation.`;
        }
    }

    send = (data: Invitation): Promise<Invitation> => {
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
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                ?slugMode=${true}
                label=${t`Name`}
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
            <ak-form-element-horizontal label=${t`Expires`} ?required=${true} name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    value="${dateTimeLocal(first(this.instance?.expires, new Date()))}"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Attributes`} name="fixedData">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.fixedData, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="singleUse">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.singleUse, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Single use`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`When enabled, the invitation will be deleted after usage.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
