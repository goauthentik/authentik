import "#elements/forms/Radio";
import "#components/ak-switch-input";
import "#elements/Alert";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/utils/TimeDeltaHelp";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { GeoipBindingEnum, NetworkBindingEnum, StagesApi, UserLoginStage } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-user-login-form")
export class UserLoginStageForm extends BaseStageForm<UserLoginStage> {
    loadInstance(pk: string): Promise<UserLoginStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesUserLoginRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: UserLoginStage): Promise<UserLoginStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesUserLoginUpdate({
                stageUuid: this.instance.pk || "",
                userLoginStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesUserLoginCreate({
            userLoginStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>${msg("Log the currently pending user in.")}</span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Session duration")}
                        required
                        name="sessionDuration"
                    >
                        <input
                            type="text"
                            value="${this.instance?.sessionDuration ?? "seconds=0"}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Determines how long a session lasts. Default of 0 seconds means that the sessions lasts until the browser is closed.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                        <ak-alert inline>
                            ${msg(
                                "Different browsers handle session cookies differently, and might not remove them even when the browser is closed.",
                            )}
                            <a
                                href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#expiresdate"
                                target="_blank"
                            >
                                ${msg("See here.")}
                            </a>
                        </ak-alert>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Stay signed in offset")}
                        required
                        name="rememberMeOffset"
                    >
                        <input
                            type="text"
                            value="${this.instance?.rememberMeOffset ?? "seconds=0"}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                'If set to a duration above 0, the user will have the option to choose to "stay signed in", which will extend their session by the time specified here.',
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Remember device")}
                        required
                        name="rememberDevice"
                    >
                        <input
                            type="text"
                            value="${this.instance?.rememberDevice ?? "days=30"}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If set to a duration above 0, a cookie will be stored for the duration specified which will allow authentik to know if the user is signing in from a new device.",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Network binding")}
                        required
                        name="networkBinding"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("No binding"),
                                    value: NetworkBindingEnum.NoBinding,
                                },
                                {
                                    label: msg("Bind ASN"),
                                    value: NetworkBindingEnum.BindAsn,
                                    default: true,
                                },
                                {
                                    label: msg("Bind ASN and Network"),
                                    value: NetworkBindingEnum.BindAsnNetwork,
                                },
                                {
                                    label: msg("Bind ASN, Network and IP"),
                                    value: NetworkBindingEnum.BindAsnNetworkIp,
                                },
                            ]}
                            .value=${this.instance?.networkBinding}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure if sessions created by this stage should be bound to the Networks they were created in.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("GeoIP binding")}
                        required
                        name="geoipBinding"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("No binding"),
                                    value: GeoipBindingEnum.NoBinding,
                                },
                                {
                                    label: msg("Bind Continent"),
                                    value: GeoipBindingEnum.BindContinent,
                                    default: true,
                                },
                                {
                                    label: msg("Bind Continent and Country"),
                                    value: GeoipBindingEnum.BindContinentCountry,
                                },
                                {
                                    label: msg("Bind Continent, Country and City"),
                                    value: GeoipBindingEnum.BindContinentCountryCity,
                                },
                            ]}
                            .value=${this.instance?.geoipBinding}
                        >
                        </ak-radio>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Configure if sessions created by this stage should be bound to their GeoIP-based location",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        name="terminateOtherSessions"
                        label=${msg("Terminate other sessions")}
                        ?checked=${this.instance?.terminateOtherSessions ?? false}
                        help=${msg(
                            "When enabled, all previous sessions of the user will be terminated.",
                        )}
                    ></ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-user-login-form": UserLoginStageForm;
    }
}
