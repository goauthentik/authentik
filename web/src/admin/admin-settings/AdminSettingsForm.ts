import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

import { AdminApi, Settings, SettingsRequest } from "@goauthentik/api";

@customElement("ak-admin-settings-form")
export class AdminSettingsForm extends Form<SettingsRequest> {
    //
    // Custom property accessors in Lit 2 require a manual call to requestUpdate(). See:
    // https://lit.dev/docs/v2/components/properties/#accessors-custom
    //
    set settings(value: Settings | undefined) {
        this._settings = value;
        this.requestUpdate();
    }

    @property({ type: Object })
    get settings() {
        return this._settings;
    }

    private _settings?: Settings;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFList);
    }

    getSuccessMessage(): string {
        return msg("Successfully updated settings.");
    }

    async send(data: SettingsRequest): Promise<Settings> {
        const result = await new AdminApi(DEFAULT_CONFIG).adminSettingsUpdate({
            settingsRequest: data,
        });
        this.dispatchEvent(new CustomEvent("ak-admin-setting-changed"));
        return result;
    }

    renderForm(): TemplateResult {
        return html`
            <ak-text-input
                name="avatars"
                label=${msg("Avatars")}
                value="${ifDefined(this._settings?.avatars)}"
                .bighelp=${html`
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Configure how authentik should show avatars for users. The following values can be set:",
                        )}
                    </p>
                    <ul class="pf-c-list">
                        <li class="pf-c-form__helper-text">
                            <code>none</code>:
                            ${msg(
                                "Disables per-user avatars and just shows a 1x1 pixel transparent picture",
                            )}
                        </li>
                        <li class="pf-c-form__helper-text">
                            <code>gravatar</code>:
                            ${msg("Uses gravatar with the user's email address")}
                        </li>
                        <li class="pf-c-form__helper-text">
                            <code>initials</code>:
                            ${msg("Generated avatars based on the user's name")}
                        </li>
                        <li class="pf-c-form__helper-text">
                            ${msg(
                                "Any URL: If you want to use images hosted on another server, you can set any URL. Additionally, these placeholders can be used:",
                            )}
                            <ul class="pf-c-list">
                                <li class="pf-c-form__helper-text">
                                    <code>%(username)s</code>: ${msg("The user's username")}
                                </li>
                                <li class="pf-c-form__helper-text">
                                    <code>%(mail_hash)s</code>:
                                    ${msg("The email address, md5 hashed")}
                                </li>
                                <li class="pf-c-form__helper-text">
                                    <code>%(upn)s</code>:
                                    ${msg("The user's UPN, if set (otherwise an empty string)")}
                                </li>
                            </ul>
                        </li>
                        <li class="pf-c-form__helper-text">
                            ${msg(
                                html`An attribute path like
                                    <code>attributes.something.avatar</code>, which can be used in
                                    combination with the file field to allow users to upload custom
                                    avatars for themselves.`,
                            )}
                        </li>
                    </ul>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "Multiple values can be set, comma-separated, and authentik will fallback to the next mode when no avatar could be found.",
                        )}
                        ${msg(
                            html`For example, setting this to <code>gravatar,initials</code> will
                                attempt to get an avatar from Gravatar, and if the user has not
                                configured on there, it will fallback to a generated avatar.`,
                        )}
                    </p>
                `}
                required
            >
            </ak-text-input>
            <ak-switch-input
                name="defaultUserChangeName"
                label=${msg("Allow users to change name")}
                ?checked="${this._settings?.defaultUserChangeName}"
                help=${msg("Enable the ability for users to change their name.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="defaultUserChangeEmail"
                label=${msg("Allow users to change email")}
                ?checked="${this._settings?.defaultUserChangeEmail}"
                help=${msg("Enable the ability for users to change their email.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="defaultUserChangeUsername"
                label=${msg("Allow users to change username")}
                ?checked="${this._settings?.defaultUserChangeUsername}"
                help=${msg("Enable the ability for users to change their username.")}
            >
            </ak-switch-input>
            <ak-text-input
                name="eventRetention"
                label=${msg("Event retention")}
                required
                value="${ifDefined(this._settings?.eventRetention)}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg("Duration after which events will be deleted from the database.")}
                    </p>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            'When using an external logging solution for archiving, this can be set to "minutes=5".',
                        )}
                    </p>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            "This setting only affects new Events, as the expiration is saved per-event.",
                        )}
                    </p>
                    <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            >
            </ak-text-input>
            <ak-form-element-horizontal label=${msg("Footer links")} name="footerLinks">
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    .value="${first(this._settings?.footerLinks, [])}"
                ></ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "This option configures the footer links on the flow executor pages. It must be a valid YAML or JSON list and can be used as follows:",
                    )}
                    <code>[{"name": "Link Name","href":"https://goauthentik.io"}]</code>
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="gdprCompliance"
                label=${msg("GDPR compliance")}
                ?checked="${this._settings?.gdprCompliance}"
                help=${msg(
                    "When enabled, all the events caused by a user will be deleted upon the user's deletion.",
                )}
            >
            </ak-switch-input>
            <ak-switch-input
                name="impersonation"
                label=${msg("Impersonation")}
                ?checked="${this._settings?.impersonation}"
                help=${msg("Globally enable/disable impersonation.")}
            >
            </ak-switch-input>
        `;
    }
}
