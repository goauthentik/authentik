import { CoreApi, User } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import YAML from "yaml";

@customElement("ak-user-form")
export class UserForm extends Form<User> {

    @property({ attribute: false })
    user?: User;

    getSuccessMessage(): string {
        if (this.user) {
            return t`Successfully updated user.`;
        } else {
            return t`Successfully created user.`;
        }
    }

    send = (data: User): Promise<User> => {
        if (this.user) {
            return new CoreApi(DEFAULT_CONFIG).coreUsersUpdate({
                id: this.user.pk || 0,
                data: data
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreUsersCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Username`}
                ?required=${true}
                name="username">
                <input type="text" value="${ifDefined(this.user?.username)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.user?.name)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`User's display name.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Email`}
                ?required=${true}
                name="email">
                <input type="email" autocomplete="off" value="${ifDefined(this.user?.email)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                name="isActive">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.user?.isActive || false}>
                    <label class="pf-c-check__label">
                        ${t`Is active`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`Designates whether this user should be treated as active. Unselect this instead of deleting accounts.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Attributes`}
                name="attributes">
                <ak-codemirror mode="yaml" value="${YAML.stringify(this.user?.attributes)}">
                </ak-codemirror>
            </ak-form-element-horizontal>
        </form>`;
    }

}
