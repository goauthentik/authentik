import { CoreApi, Group } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "@polymer/paper-input/paper-input";
import "@polymer/iron-form/iron-form";
import '@polymer/paper-checkbox/paper-checkbox';
import '@polymer/paper-dropdown-menu/paper-dropdown-menu';
import '@polymer/paper-listbox/paper-listbox';
import '@polymer/paper-item/paper-item';
import { until } from "lit-html/directives/until";

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
                <paper-dropdown-menu label=${gettext("Parent")} horizontal-align="left">
                    <paper-listbox slot="dropdown-content" name="parent" ?alwaysFloatLabel=${true} selected=${this.group?.parent} attr-for-selected="uuid">
                        <paper-item uuid=${null}>${gettext("No parent")}</paper-item>
                        ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then(groups => {
                            return groups.results.map(group => {
                                return html`<paper-item uuid=${group.pk}>${group.name}</paper-item>`;
                            })
                        }), html``)}
                    </paper-listbox>
                </paper-dropdown-menu>
                <div class="pf-c-form__group">
                    <div class="pf-c-form__group-label">
                        <label class="pf-c-form__label">
                            <span class="pf-c-form__label-text">${gettext("Members")}</span>
                        </label>
                    </div>
                    <div class="pf-c-form__group-control">
                        <div class="pf-c-form__horizontal-group">
                            <select name="users" class="pf-c-form-control" multiple="">
                                ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({}).then(users => {
                                    return users.results.map(user => {
                                        const selected = this.group?.users.some(su => {
                                            return su.pk == user.pk;
                                        });
                                        return html`<option ?selected=${selected}>${user.username}</option>`;
                                    });
                                }))}
                            </select>
                            <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
                        </div>
                    </div>
                </div>
            </form>`;
    }

}
