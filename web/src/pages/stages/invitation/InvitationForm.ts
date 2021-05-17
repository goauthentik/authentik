import { Invitation, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/CodeMirror";
import YAML from "yaml";
import { first } from "../../../utils";
import { ModelForm } from "../../../elements/forms/ModelForm";

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
                invitationRequest: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsCreate({
                invitationRequest: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Expires`}
                ?required=${true}
                name="expires">
                <input type="date" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Attributes`}
                name="fixedData">
                <ak-codemirror mode="yaml" value="${YAML.stringify(first(this.instance?.fixedData, {}))}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${t`Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="singleUse">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${first(this.instance?.singleUse, true)}>
                    <label class="pf-c-check__label">
                        ${t`Single use`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`When enabled, the invitation will be deleted after usage.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
