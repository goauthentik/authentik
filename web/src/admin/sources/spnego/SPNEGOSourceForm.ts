import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-source-flow-search";
import { iconHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import { UserMatchingModeToLabel } from "@goauthentik/admin/sources/oauth/utils";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    SPNEGOSource,
    SourcesApi,
    UserMatchingModeEnum,
} from "@goauthentik/api";

@customElement("ak-source-spnego-form")
export class SPNEGOSourceForm extends WithCapabilitiesConfig(BaseSourceForm<SPNEGOSource>) {
    @state()
    clearIcon = false;

    async loadInstance(pk: string): Promise<SPNEGOSource> {
        const source = await new SourcesApi(DEFAULT_CONFIG).sourcesSpnegoRetrieve({
            slug: pk,
        });
        this.clearIcon = false;
        return source;
    }

    async send(data: SPNEGOSource): Promise<SPNEGOSource> {
        let source: SPNEGOSource;
        if (this.instance) {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesSpnegoUpdate({
                slug: this.instance.slug,
                sPNEGOSourceRequest: data,
            });
        } else {
            source = await new SourcesApi(DEFAULT_CONFIG).sourcesSpnegoCreate({
                sPNEGOSourceRequest: data,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["icon"];
            if (icon || this.clearIcon) {
                await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconCreate({
                    slug: source.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new SourcesApi(DEFAULT_CONFIG).sourcesAllSetIconUrlCreate({
                slug: source.slug,
                filePathRequest: {
                    url: data.icon || "",
                },
            });
        }
        return source;
    }

    renderForm(): TemplateResult {
        return html` <ak-text-input
                name="name"
                label=${msg("Name")}
                value=${ifDefined(this.instance?.name)}
                required
            >
            </ak-text-input>
            <ak-text-input
                name="slug"
                label=${msg("Slug")}
                value=${ifDefined(this.instance?.slug)}
                required
            >
            </ak-text-input>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${first(this.instance?.enabled, true)}
            >
            </ak-switch-input>
            <ak-form-element-horizontal
                label=${msg("User matching mode")}
                ?required=${true}
                name="userMatchingMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${UserMatchingModeEnum.Identifier}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.Identifier}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.Identifier)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.EmailDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.EmailDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.EmailDeny)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameLink}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameLink}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameLink)}
                    </option>
                    <option
                        value=${UserMatchingModeEnum.UsernameDeny}
                        ?selected=${this.instance?.userMatchingMode ===
                        UserMatchingModeEnum.UsernameDeny}
                    >
                        ${UserMatchingModeToLabel(UserMatchingModeEnum.UsernameDeny)}
                    </option>
                </select>
            </ak-form-element-horizontal>
            ${this.can(CapabilitiesEnum.CanSaveMedia)
                ? html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                          <input type="file" value="" class="pf-c-form-control" />
                          ${this.instance?.icon
                              ? html`
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Currently set to:")} ${this.instance?.icon}
                                    </p>
                                `
                              : html``}
                      </ak-form-element-horizontal>
                      ${this.instance?.icon
                          ? html`
                                <ak-form-element-horizontal>
                                    <label class="pf-c-switch">
                                        <input
                                            class="pf-c-switch__input"
                                            type="checkbox"
                                            @change=${(ev: Event) => {
                                                const target = ev.target as HTMLInputElement;
                                                this.clearIcon = target.checked;
                                            }}
                                        />
                                        <span class="pf-c-switch__toggle">
                                            <span class="pf-c-switch__toggle-icon">
                                                <i class="fas fa-check" aria-hidden="true"></i>
                                            </span>
                                        </span>
                                        <span class="pf-c-switch__label">
                                            ${msg("Clear icon")}
                                        </span>
                                    </label>
                                    <p class="pf-c-form__helper-text">
                                        ${msg("Delete currently set icon.")}
                                    </p>
                                </ak-form-element-horizontal>
                            `
                          : html``}`
                : html`<ak-form-element-horizontal label=${msg("Icon")} name="icon">
                      <input
                          type="text"
                          value="${first(this.instance?.icon, "")}"
                          class="pf-c-form-control"
                      />
                      <p class="pf-c-form__helper-text">${iconHelperText}</p>
                  </ak-form-element-horizontal>`}

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-textarea-input
                        name="keytab"
                        label=${msg("Keytab")}
                        value=${ifDefined(this.instance?.keytab)}
                        help=${msg(
                            "Keytab to use for this provider. Must be base64-encoded. You can also specify a keytab with the format TYPE:residual.",
                        )}
                    >
                    </ak-textarea-input>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="serverName"
                        label=${msg("Server name")}
                        value=${ifDefined(this.instance?.serverName)}
                        help=${msg(
                            "Server name to use. Leave empty to try all entries in the keytab or credentials cache.",
                        )}
                    >
                    </ak-text-input>
                    <ak-text-input
                        name="ccache"
                        label=${msg("Credentials cache")}
                        value=${ifDefined(this.instance?.ccache)}
                        help=${msg(
                            "Credentials cache to use for server credentials. Must be of the form TYPE:residual. Leave empty to use the default of creating a credential cache unique to this source.",
                        )}
                    >
                    </ak-text-input>
                    <ak-switch-input
                        name="guessEmail"
                        label=${msg("Guess email")}
                        ?checked=${first(this.instance?.guessEmail, false)}
                        help=${msg(
                            "Whether to guess the user email based on their realm for enrollment.",
                        )}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Flow settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Authentication flow")}
                        ?required=${true}
                        name="authenticationFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Authentication}
                            .currentFlow=${this.instance?.authenticationFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-authentication"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when authenticating existing users.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Enrollment flow")}
                        ?required=${true}
                        name="enrollmentFlow"
                    >
                        <ak-source-flow-search
                            flowType=${FlowsInstancesListDesignationEnum.Enrollment}
                            .currentFlow=${this.instance?.enrollmentFlow}
                            .instanceId=${this.instance?.pk}
                            fallback="default-source-enrollment"
                        ></ak-source-flow-search>
                        <p class="pf-c-form__helper-text">
                            ${msg("Flow to use when enrolling new users.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
