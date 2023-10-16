import "@goauthentik/admin/applications/ProviderSelectModal";
import { iconHelperText } from "@goauthentik/admin/helperText";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first, groupBy } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    Application,
    CapabilitiesEnum,
    CoreApi,
    PolicyEngineMode,
    Provider,
    ProvidersAllListRequest,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-application-form")
export class ApplicationForm extends ModelForm<Application, string> {
    async loadInstance(pk: string): Promise<Application> {
        const app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsRetrieve({
            slug: pk,
        });
        this.clearIcon = false;
        this.backchannelProviders = app.backchannelProvidersObj || [];
        return app;
    }

    @property({ attribute: false })
    provider?: number;

    @state()
    backchannelProviders: Provider[] = [];

    @property({ type: Boolean })
    clearIcon = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated application.");
        } else {
            return msg("Successfully created application.");
        }
    }

    async send(data: Application): Promise<Application | void> {
        let app: Application;
        data.backchannelProviders = this.backchannelProviders.map((p) => p.pk);
        if (this.instance) {
            app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsUpdate({
                slug: this.instance.slug,
                applicationRequest: data,
            });
        } else {
            app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsCreate({
                applicationRequest: data,
            });
        }
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["metaIcon"];
            if (icon || this.clearIcon) {
                await new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconCreate({
                    slug: app.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconUrlCreate({
                slug: app.slug,
                filePathRequest: {
                    url: data.metaIcon || "",
                },
            });
        }
        return app;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${msg("Application's display Name.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Internal application name, used in URLs.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Group")} name="group">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.group)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Provider")} name="provider">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Provider[]> => {
                        const args: ProvidersAllListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const items = await new ProvidersApi(DEFAULT_CONFIG).providersAllList(args);
                        return items.results;
                    }}
                    .renderElement=${(item: Provider): string => {
                        return item.name;
                    }}
                    .value=${(item: Provider | undefined): number | undefined => {
                        return item?.pk;
                    }}
                    .groupBy=${(items: Provider[]) => {
                        return groupBy(items, (item) => item.verboseName);
                    }}
                    .selected=${(item: Provider): boolean => {
                        return this.instance?.provider === item.pk;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg("Select a provider that this application should use.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                label=${msg("Backchannel providers")}
                name="backchannelProviders"
            >
                <div class="pf-c-input-group">
                    <ak-provider-select-table
                        ?backchannelOnly=${true}
                        .confirm=${(items: Provider[]) => {
                            this.backchannelProviders = items;
                            this.requestUpdate();
                            return Promise.resolve();
                        }}
                    >
                        <button slot="trigger" class="pf-c-button pf-m-control" type="button">
                            <pf-tooltip position="top" content=${msg("Add provider")}>
                                <i class="fas fa-plus" aria-hidden="true"></i>
                            </pf-tooltip>
                        </button>
                    </ak-provider-select-table>
                    <div class="pf-c-form-control">
                        <ak-chip-group>
                            ${this.backchannelProviders.map((provider) => {
                                return html`<ak-chip
                                    .removable=${true}
                                    value=${ifDefined(provider.pk)}
                                    @remove=${() => {
                                        const idx = this.backchannelProviders.indexOf(provider);
                                        this.backchannelProviders.splice(idx, 1);
                                        this.requestUpdate();
                                    }}
                                >
                                    ${provider.name}
                                </ak-chip>`;
                            })}
                        </ak-chip-group>
                    </div>
                </div>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select backchannel providers which augment the functionality of the main provider.",
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                label=${msg("Policy engine mode")}
                ?required=${true}
                name="policyEngineMode"
            >
                <ak-radio
                    .options=${[
                        {
                            label: "any",
                            value: PolicyEngineMode.Any,
                            default: true,
                            description: html`${msg("Any policy must match to grant access")}`,
                        },
                        {
                            label: "all",
                            value: PolicyEngineMode.All,
                            description: html`${msg("All policies must match to grant access")}`,
                        },
                    ]}
                    .value=${this.instance?.policyEngineMode}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-group>
                <span slot="header"> ${msg("UI settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Launch URL")} name="metaLaunchUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.metaLaunchUrl)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If left empty, authentik will try to extract the launch URL based on the selected provider.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="openInNewTab">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.openInNewTab, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Open in new tab")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "If checked, the launch URL will open in a new browser tab or window from the user's application library.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    ${rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanSaveMedia)
                        ? html`<ak-form-element-horizontal label="${msg("Icon")}" name="metaIcon">
                                  <input type="file" value="" class="pf-c-form-control" />
                                  ${this.instance?.metaIcon
                                      ? html`
                                            <p class="pf-c-form__helper-text">
                                                ${msg("Currently set to:")}
                                                ${this.instance?.metaIcon}
                                            </p>
                                        `
                                      : html``}
                              </ak-form-element-horizontal>
                              ${this.instance?.metaIcon
                                  ? html`
                                        <ak-form-element-horizontal>
                                            <label class="pf-c-switch">
                                                <input
                                                    class="pf-c-switch__input"
                                                    type="checkbox"
                                                    @change=${(ev: Event) => {
                                                        const target =
                                                            ev.target as HTMLInputElement;
                                                        this.clearIcon = target.checked;
                                                    }}
                                                />
                                                <span class="pf-c-switch__toggle">
                                                    <span class="pf-c-switch__toggle-icon">
                                                        <i
                                                            class="fas fa-check"
                                                            aria-hidden="true"
                                                        ></i>
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
                        : html`<ak-form-element-horizontal label=${msg("Icon")} name="metaIcon">
                              <input
                                  type="text"
                                  value="${first(this.instance?.metaIcon, "")}"
                                  class="pf-c-form-control"
                              />
                              <p class="pf-c-form__helper-text">${iconHelperText}</p>
                          </ak-form-element-horizontal>`}
                    <ak-form-element-horizontal label=${msg("Publisher")} name="metaPublisher">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.metaPublisher)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Description")} name="metaDescription">
                        <textarea class="pf-c-form-control">
${ifDefined(this.instance?.metaDescription)}</textarea
                        >
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
