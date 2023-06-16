import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { dateTimeLocal, first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { CoreApi, CoreUsersListRequest, IntentEnum, Token, User } from "@goauthentik/api";

@customElement("ak-token-form")
export class TokenForm extends ModelForm<Token, string> {
    loadInstance(pk: string): Promise<Token> {
        return new CoreApi(DEFAULT_CONFIG).coreTokensRetrieve({
            identifier: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated token.");
        } else {
            return msg("Successfully created token.");
        }
    }

    async send(data: Token): Promise<Token> {
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
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${msg("Identifier")}
                name="identifier"
                ?required=${true}
            >
                <input
                    type="text"
                    value="${first(this.instance?.identifier, "")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Unique identifier the token is referenced by.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("User")} ?required=${true} name="user">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): TemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
                    }}
                    .selected=${(user: User): boolean => {
                        return this.instance?.user === user.pk;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Intent")} ?required=${true} name="intent">
                <ak-radio
                    .options=${[
                        {
                            label: msg("API Token"),
                            value: IntentEnum.Api,
                            default: true,
                            description: html`${msg("Used to access the API programmatically")}`,
                        },
                        {
                            label: msg("App password."),
                            value: IntentEnum.AppPassword,
                            description: html`${msg("Used to login using a flow executor")}`,
                        },
                    ]}
                    .value=${this.instance?.intent}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Description")} name="description">
                <input
                    type="text"
                    value="${first(this.instance?.description, "")}"
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="expiring">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.expiring, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Expiring")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If this is selected, the token will expire. Upon expiration, the token will be rotated.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Expires on")} name="expires">
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
