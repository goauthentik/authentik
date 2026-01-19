import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { dateTimeLocal } from "#common/temporal";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import { CoreApi, CoreUsersListRequest, IntentEnum, Token, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

const EXPIRATION_DURATION = 30 * 60 * 1000; // 30 minutes

@customElement("ak-token-form")
export class TokenForm extends ModelForm<Token, string> {
    protected expirationMinimumDate = new Date();

    @state()
    protected expiresAt: Date | null = new Date(Date.now() + EXPIRATION_DURATION);

    reset(): void {
        super.reset();
        this.expiresAt = new Date(Date.now() + EXPIRATION_DURATION);
    }

    async loadInstance(pk: string): Promise<Token> {
        const token = await new CoreApi(DEFAULT_CONFIG).coreTokensRetrieve({
            identifier: pk,
        });

        this.expiresAt = token.expiring
            ? new Date(token.expires || Date.now() + EXPIRATION_DURATION)
            : null;

        return token;
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated token.")
            : msg("Successfully created token.");
    }

    async send(data: Token): Promise<Token> {
        if (this.instance?.identifier) {
            return new CoreApi(DEFAULT_CONFIG).coreTokensUpdate({
                identifier: this.instance.identifier,
                tokenRequest: data,
            });
        }
        return new CoreApi(DEFAULT_CONFIG).coreTokensCreate({
            tokenRequest: data,
        });
    }

    //#region Event Listeners

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;

        if (!expiringElement.checked) {
            this.expiresAt = null;
            return;
        }

        if (this.instance?.expiring && this.instance.expires) {
            this.expiresAt = new Date(this.instance.expires);
            return;
        }

        this.expiresAt = new Date(Date.now() + EXPIRATION_DURATION);
    };

    //#endregion

    //#region Renders

    renderForm(): TemplateResult {
        return html`<ak-text-input
                name="identifier"
                value="${this.instance?.identifier ?? ""}"
                label=${msg("Identifier")}
                placeholder=${msg("Type a unique identifier...")}
                spellcheck="false"
                input-hint="code"
                required
                ?autofocus=${!this.instance}
                help=${msg("Unique identifier the token is referenced by.")}
            ></ak-text-input>

            <ak-form-element-horizontal label=${msg("User")} required name="user">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };

                        if (typeof query !== "undefined") {
                            args.search = query;
                        }

                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        const instanceUser = this.instance?.userObj;

                        if (!instanceUser) {
                            return users.results;
                        }

                        if (users.results.find((user) => user.pk === instanceUser.pk)) {
                            return users.results;
                        }

                        return [instanceUser, ...users.results];
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
            <ak-form-element-horizontal label=${msg("Intent")} required name="intent">
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

            <ak-text-input
                name="description"
                value="${this.instance?.description ?? ""}"
                label=${msg("Description")}
                placeholder=${msg("Type a token description...")}
            ></ak-text-input>

            <ak-switch-input
                name="expiring"
                label=${msg("Expiring")}
                help=${msg(
                    "Whether the token will expire. Upon expiration, the token will be rotated.",
                )}
                @change=${this.#expiringChangeListener}
                ?checked=${this.expiresAt}
            ></ak-switch-input>

            <ak-form-element-horizontal name="expires">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="expiration-date-input"
                    type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    min=${dateTimeLocal(this.expirationMinimumDate)}
                    ?disabled=${!this.expiresAt}
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-token-form": TokenForm;
    }
}
