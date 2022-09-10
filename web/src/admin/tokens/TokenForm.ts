import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/FormGroup";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/web/elements/forms/ModelForm";
import { UserOption } from "@goauthentik/web/elements/user/utils";
import { dateTimeLocal, first } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import { CoreApi, IntentEnum, Token } from "@goauthentik/api";

@customElement("ak-token-form")
export class TokenForm extends ModelForm<Token, string> {
    loadInstance(pk: string): Promise<Token> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensRetrieve({
            identifier: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated token.`;
        } else {
            return t`Successfully created token.`;
        }
    }

    send = (data: Token): Promise<Token> => {
        if (this.instance?.identifier) {
            return new CoreApi(DEFAULT_CONFIG).coreTokensUpdate({
                identifier: this.instance.identifier,
                tokenRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
                tokenRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Identifier`} name="identifier" ?required=${true}>
                <input
                    type="text"
                    value="${first(this.instance?.identifier, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Unique identifier the token is referenced by.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`User`} ?required=${true} name="user">
                <select class="pf-c-form-control">
                    ${until(
                        new CoreApi(DEFAULT_CONFIG)
                            .coreUsersList({
                                ordering: "username",
                            })
                            .then((users) => {
                                return users.results.map((user) => {
                                    return html`<option
                                        value=${user.pk}
                                        ?selected=${this.instance?.user === user.pk}
                                    >
                                        ${UserOption(user)}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Intent`} ?required=${true} name="intent">
                <select class="pf-c-form-control">
                    <option
                        value=${IntentEnum.Api}
                        ?selected=${this.instance?.intent === IntentEnum.Api}
                    >
                        ${t`API Token (can be used to access the API programmatically)`}
                    </option>
                    <option
                        value=${IntentEnum.AppPassword}
                        ?selected=${this.instance?.intent === IntentEnum.AppPassword}
                    >
                        ${t`App password (can be used to login using a flow executor)`}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Description`} name="description">
                <input
                    type="text"
                    value="${first(this.instance?.description, "")}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="expiring">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.expiring, true)}
                    />
                    <label class="pf-c-check__label"> ${t`Expiring?`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`If this is selected, the token will expire. Upon expiration, the token will be rotated.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Expires on`} name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    value="${dateTimeLocal(first(this.instance?.expires, new Date()))}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
