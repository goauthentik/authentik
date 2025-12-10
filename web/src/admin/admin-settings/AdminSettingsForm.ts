import "#components/ak-number-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/ak-array-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import "./AdminSettingsFooterLinks.js";

import { akFooterLinkInput, IFooterLinkInput } from "./AdminSettingsFooterLinks.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import { AdminApi, FooterLink, Settings, SettingsRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

const DEFAULT_REPUTATION_LOWER_LIMIT = -5;
const DEFAULT_REPUTATION_UPPER_LIMIT = 5;

@customElement("ak-admin-settings-form")
export class AdminSettingsForm extends Form<SettingsRequest> {
    public static styles: CSSResult[] = [
        ...super.styles,
        PFList,
        css`
            ak-array-input {
                width: 100%;
            }
        `,
    ];

    @property({ attribute: false })
    public settings!: Settings;

    getSuccessMessage(): string {
        return msg("Successfully updated settings.");
    }

    async send(settingsRequest: SettingsRequest): Promise<Settings> {
        const result = await new AdminApi(DEFAULT_CONFIG).adminSettingsUpdate({
            settingsRequest,
        });

        this.dispatchEvent(new CustomEvent("ak-admin-setting-changed"));

        return result;
    }

    renderForm(): TemplateResult {
        const { settings } = this;

        return html`
            <ak-text-input
                name="avatars"
                label=${msg("Avatars")}
                value="${ifDefined(settings.avatars)}"
                input-hint="code"
                required
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
            >
            </ak-text-input>
            <ak-switch-input
                name="defaultUserChangeName"
                label=${msg("Allow users to change name")}
                ?checked=${settings.defaultUserChangeName}
                help=${msg("Enable the ability for users to change their name.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="defaultUserChangeEmail"
                label=${msg("Allow users to change email")}
                ?checked=${settings.defaultUserChangeEmail}
                help=${msg("Enable the ability for users to change their email.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="defaultUserChangeUsername"
                label=${msg("Allow users to change username")}
                ?checked=${settings.defaultUserChangeUsername}
                help=${msg("Enable the ability for users to change their username.")}
            >
            </ak-switch-input>
            <ak-text-input
                name="eventRetention"
                label=${msg("Event retention")}
                input-hint="code"
                required
                value="${ifDefined(settings.eventRetention)}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg("Duration after which events will be deleted from the database.")}
                    </p>
                    <p class="pf-c-form__helper-text">
                        ${msg(
                            html`When using an external logging solution for archiving, this can be
                                set to <code>minutes=5</code>.`,
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
            <ak-number-input
                label=${msg("Reputation: lower limit")}
                required
                name="reputationLowerLimit"
                value="${settings.reputationLowerLimit ?? DEFAULT_REPUTATION_LOWER_LIMIT}"
                help=${msg("Reputation cannot decrease lower than this value. Zero or negative.")}
            ></ak-number-input>
            <ak-number-input
                label=${msg("Reputation: upper limit")}
                required
                name="reputationUpperLimit"
                value="${settings.reputationUpperLimit ?? DEFAULT_REPUTATION_UPPER_LIMIT}"
                help=${msg("Reputation cannot increase higher than this value. Zero or positive.")}
            ></ak-number-input>
            <ak-form-element-horizontal label=${msg("Footer links")} name="footerLinks">
                <ak-array-input
                    .items=${settings.footerLinks ?? []}
                    .newItem=${() => ({ name: "", href: "" })}
                    .row=${(f?: FooterLink) =>
                        akFooterLinkInput({
                            ".footerLink": f,
                            "style": "width: 100%",
                            "name": "footer-link",
                        } as unknown as IFooterLinkInput)}
                >
                </ak-array-input>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "This option configures the footer links on the flow executor pages. The URL is limited to web and mail addresses. If the name is left blank, the URL will be shown.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="gdprCompliance"
                label=${msg("GDPR compliance")}
                ?checked=${settings.gdprCompliance}
                help=${msg(
                    "When enabled, all the events caused by a user will be deleted upon the user's deletion.",
                )}
            >
            </ak-switch-input>
            <ak-switch-input
                name="impersonation"
                label=${msg("Impersonation")}
                ?checked=${settings.impersonation}
                help=${msg("Globally enable/disable impersonation.")}
            >
            </ak-switch-input>
            <ak-switch-input
                name="impersonationRequireReason"
                label=${msg("Require reason for impersonation")}
                ?checked=${settings.impersonationRequireReason}
                help=${msg("Require administrators to provide a reason for impersonating a user.")}
            >
            </ak-switch-input>
            <ak-text-input
                name="defaultTokenDuration"
                label=${msg("Default token duration")}
                input-hint="code"
                required
                value="${ifDefined(settings.defaultTokenDuration)}"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                        ${msg("Default duration for generated tokens")}
                    </p>
                    <ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            >
            </ak-text-input>
            <ak-number-input
                label=${msg("Default token length")}
                required
                name="defaultTokenLength"
                value="${settings.defaultTokenLength ?? 60}"
                help=${msg("Default length of generated tokens")}
            ></ak-number-input>
            <ak-form-group
                label=${msg("Flags")}
                description=${msg(
                    "Flags allow you to enable new functionality and behaviour in authentik early.",
                )}
            >
                <div class="pf-c-form">
                    <ak-switch-input
                        name="flags.policiesBufferedAccessView"
                        ?checked=${settings?.flags.policiesBufferedAccessView ?? false}
                        label=${msg("Buffer PolicyAccessVew requests")}
                        help=${msg(
                            "When enabled, parallel requests for application authorization will be buffered instead of conflicting with other flows.",
                        )}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="flags.flowsRefreshOthers"
                        ?checked=${settings?.flags.flowsRefreshOthers ?? false}
                        label=${msg("Refresh other flow tabs upon authentication")}
                        help=${msg(
                            "When enabled, other flow tabs in a session will refresh upon a successful authentication.",
                        )}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-settings-form": AdminSettingsForm;
    }
}
