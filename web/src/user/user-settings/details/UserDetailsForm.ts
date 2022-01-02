import { i18n } from "@lingui/core";
import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, UserSelf } from "@goauthentik/api";

import { DEFAULT_CONFIG, tenant } from "../../../api/Config";
import { me } from "../../../api/Users";
import { getConfigForUser, uiConfig } from "../../../common/config";
import "../../../elements/EmptyState";
import "../../../elements/forms/Form";
import "../../../elements/forms/FormElement";
import "../../../elements/forms/HorizontalFormElement";
import { ModelForm } from "../../../elements/forms/ModelForm";
import { LOCALES, autoDetectLanguage } from "../../../interfaces/locale";

@customElement("ak-user-details-form")
export class UserDetailsForm extends ModelForm<UserSelf, number> {
    currentLocale?: string;

    viewportCheck = false;

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    loadInstance(pk: number): Promise<UserSelf> {
        return me().then((user) => {
            const config = getConfigForUser(user.user);
            this.currentLocale = config.locale;
            return user.user;
        });
    }

    getSuccessMessage(): string {
        return t`Successfully updated details.`;
    }

    send = (data: UserSelf): Promise<UserSelf> => {
        const newConfig = getConfigForUser(data);
        const newLocale = LOCALES.find((locale) => locale.code === newConfig.locale);
        if (newLocale) {
            i18n.activate(newLocale.code);
        } else if (newConfig.locale === "") {
            autoDetectLanguage();
        } else {
            console.debug(`authentik/user: invalid locale: '${newConfig.locale}'`);
        }
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
        return html`${until(
            uiConfig().then((config) => {
                return html`<form class="pf-c-form pf-m-horizontal">
                    <ak-form-element-horizontal
                        label=${t`Username`}
                        ?required=${true}
                        name="username"
                    >
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
                    <ak-form-element-horizontal label=${t`Locale`} name="settings.locale">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${config.locale === ""}>
                                ${t`Auto-detect (based on your browser)`}
                            </option>
                            ${LOCALES.map((locale) => {
                                return html`<option
                                    value=${locale.code}
                                    ?selected=${config.locale === locale.code}
                                >
                                    ${locale.label}
                                </option>`;
                            })}
                        </select>
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
            }),
        )}`;
    }
}
