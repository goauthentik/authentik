import { CoreApi, Group } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import YAML from "yaml";

@customElement("ak-group-form")
export class GroupForm extends Form<Group> {

    @property({attribute: false})
    group?: Group;

    getSuccessMessage(): string {
        if (this.group) {
            return gettext("Successfully updated group.");
        } else {
            return gettext("Successfully created group.");
        }
    }

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
            <ak-form-element-horizontal label=${gettext("Name")} ?required=${true}>
                <input type="text" name="name" value="${ifDefined(this.group?.name)}" class="pf-c-form-control" required="">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal>
                <div class="pf-c-check">
                    <input type="checkbox" name="is_superuser" class="pf-c-check__input" ?checked=${this.group?.isSuperuser || false}>
                    <label class="pf-c-check__label">
                        ${gettext("Is superuser")}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${gettext("Users added to this group will be superusers.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${gettext("Parent")} ?required=${true}>
                <select name="parent" class="pf-c-form-control">
                    <option value="" ?selected=${this.group?.parent === undefined}>---------</option>
                    ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then(groups => {
                        return groups.results.map(group => {
                            return html`<option value=${ifDefined(group.pk)} ?selected=${this.group?.parent === group.pk}>${group.name}</option>`;
                        });
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${gettext("Members")} ?required=${true}>
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
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${gettext("Attributes")}>
                <ak-codemirror mode="yaml" name="attributes" value="${YAML.stringify(this.group?.attributes)}">
                </ak-codemirror>
            </ak-form-element-horizontal>
        </form>`;
    }

}
