import { CoreApi, Group } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "@polymer/paper-input/paper-input";
import "@polymer/iron-form/iron-form";
import '@polymer/paper-checkbox/paper-checkbox.js';

@customElement("ak-group-form")
export class GroupForm extends Form<Group> {

    @property({attribute: false})
    group?: Group;

    send = (data: Group): Promise<Group> => {
        if (this.group) {
            return new CoreApi(DEFAULT_CONFIG).coreGroupsUpdate({
                groupUuid: this.group.pk || "",
                data: data
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreGroupsCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
                <paper-input
                    name="name"
                    ?alwaysFloatLabel=${true}
                    label="${gettext("Name")}"
                    value=${ifDefined(this.group?.name)}>
                </paper-input>
                <paper-checkbox
                    name="isSuperuser"
                    ?alwaysFloatLabel=${true}
                    ?checked=${this.group?.isSuperuser || false}>
                    ${gettext("Is superuser")}
                </paper-checkbox>
                <p class="pf-c-form__helper-text">${gettext("Users added to this group will be superusers.")}</p>
            </form>`;
    }

}
