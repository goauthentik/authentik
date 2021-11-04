import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, UserSelf } from "@goauthentik/api";

import { DEFAULT_CONFIG, tenant } from "../../../api/Config";
import { me } from "../../../api/Users";
import "../../../elements/EmptyState";
import "../../../elements/forms/Form";
import "../../../elements/forms/FormElement";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-user-details-form")
export class UserDetailsForm extends ModelForm<UserSelf, number> {
    viewportCheck = false;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    loadInstance(pk: number): Promise<UserSelf> {
        return me().then((user) => {
            return user.user;
        });
    }

    getSuccessMessage(): string {
        return t`Successfully updated details.`;
    }

    send = (data: UserSelf): Promise<UserSelf> => {
        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersUpdateSelfUpdate({
                userSelfRequest: data,
            })
            .then((su) => {
                return su.user;
            });
    };

    renderForm(): TemplateResult {
        if (!this.instance) {
            return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
        }
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Username`} ?required=${true} name="username">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.username)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Name`} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">${t`User's display name.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Email`} name="email">
                <input
                    type="email"
                    value="${ifDefined(this.instance?.email)}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>

            <div class="pf-c-form__group pf-m-action">
                <div class="pf-c-form__horizontal-group">
                    <div class="pf-c-form__actions">
                        <button
                            @click=${(ev: Event) => {
                                return this.submit(ev);
                            }}
                            class="pf-c-button pf-m-primary"
                        >
                            ${t`Save`}
                        </button>
                        ${until(
                            tenant().then((tenant) => {
                                if (tenant.flowUnenrollment) {
                                    return html`<a
                                        class="pf-c-button pf-m-danger"
                                        href="/if/flow/${tenant.flowUnenrollment}"
                                    >
                                        ${t`Delete account`}
                                    </a>`;
                                }
                                return html``;
                            }),
                        )}
                    </div>
                </div>
            </div>
        </form>`;
    }
}
