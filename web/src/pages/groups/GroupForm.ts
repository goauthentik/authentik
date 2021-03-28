import { CoreApi, Group } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { formGroup } from "../../elements/forms/utils";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-group-form")
export class GroupForm extends Form<Group> {

    @property({attribute: false})
    group?: Group;

    successMessage = gettext("Successfully updated group");

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
                ${formGroup(gettext("Name"), html`
                    <input type="text" name="name" value="${ifDefined(this.group?.name)}" class="pf-c-form-control" required="">
                `)}
                ${formGroup("", html`
                    <div class="pf-c-check">
                        <input type="checkbox" name="is_superuser" class="pf-c-check__input" ?checked=${this.group?.isSuperuser || false}>
                        <label class="pf-c-check__label">
                            ${gettext("Is superuser")}
                        </label>
                    </div>
                    <p class="pf-c-form__helper-text">${gettext("Users added to this group will be superusers.")}</p>
                `)}
                ${formGroup(gettext("Parent"), html`
                    <select name="parent" class="pf-c-form-control">
                        <option value="" ?selected=${this.group?.parent === undefined}>---------</option>
                        ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then(groups => {
                            return groups.results.map(group => {
                                return html`<option value=${ifDefined(group.pk)} ?selected=${this.group?.parent === group.pk}>${group.name}</option>`;
                            });
                        }), html``)}
                    </select>
                `)}
                ${formGroup(gettext("Members"), html`
                    <select name="users" class="pf-c-form-control" multiple="">
                        ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({}).then(users => {
                            return users.results.map(user => {
                                const selected = Array.from(this.group?.users || []).some(su => {
                                    return su == user.pk;
                                });
                                return html`<option value=${ifDefined(user.pk)} ?selected=${selected}>${user.username}</option>`;
                            });
                        }))}
                    </select>
                    <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
                `)}
            </form>`;
    }

}
