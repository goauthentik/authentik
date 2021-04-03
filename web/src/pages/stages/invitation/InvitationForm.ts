import { Invitation, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/CodeMirror";
import YAML from "yaml";

@customElement("ak-invitation-form")
export class InvitationForm extends Form<Invitation> {

    @property({attribute: false})
    invitation?: Invitation;

    getSuccessMessage(): string {
        if (this.invitation) {
            return gettext("Successfully updated invitation.");
        } else {
            return gettext("Successfully created invitation.");
        }
    }

    send = (data: Invitation): Promise<Invitation> => {
        if (this.invitation) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUpdate({
                inviteUuid: this.invitation.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Expires")}
                ?required=${true}
                name="expires">
                <input type="date" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Attributes")}
                name="fixedData">
                <ak-codemirror mode="yaml" value="${YAML.stringify(this.invitation?.fixedData)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${gettext("Optional data which is loaded into the flow's 'prompt_data' context variable.")}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
