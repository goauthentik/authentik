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

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
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
        return app;
    }

    @property({ attribute: false })
    provider?: number;

    @property({ type: Boolean })
    clearIcon = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated application.`;
        } else {
            return t`Successfully created application.`;
        }
    }

    async send(data: Application): Promise<Application | void> {
        let app: Application;
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
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Application's display Name.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Slug`} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${t`Internal application name, used in URLs.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Group`} name="group">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.group)}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`Optionally enter a group name. Applications with identical groups are shown grouped together.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Provider`} name="provider">
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
                    ${t`Select a provider that this application should use.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode"
            >
                <ak-radio
                    .options=${[
                        {
                            label: "ANY",
                            value: PolicyEngineMode.Any,
                            default: true,
                            description: html`${t`Any policy must match to grant access`}`,
                        },
                        {
                            label: "ALL",
                            value: PolicyEngineMode.All,
                            description: html`${t`All policies must match to grant access`}`,
                        },
                    ]}
                    .value=${this.instance?.policyEngineMode}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-group>
                <span slot="header"> ${t`UI settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Launch URL`} name="metaLaunchUrl">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.metaLaunchUrl)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`If left empty, authentik will try to extract the launch URL based on the selected provider.`}
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
                            <span class="pf-c-switch__label">${t`Open in new tab`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`If checked, the launch URL will open in a new browser tab or window from the user's application library.`}
                        </p>
                    </ak-form-element-horizontal>
                    ${rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanSaveMedia)
                        ? html`<ak-form-element-horizontal label=${t`Icon`} name="metaIcon">
                                  <input type="file" value="" class="pf-c-form-control" />
                                  ${this.instance?.metaIcon
                                      ? html`
                                            <p class="pf-c-form__helper-text">
                                                ${t`Currently set to:`} ${this.instance?.metaIcon}
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
                                                    ${t`Clear icon`}
                                                </span>
                                            </label>
                                            <p class="pf-c-form__helper-text">
                                                ${t`Delete currently set icon.`}
                                            </p>
                                        </ak-form-element-horizontal>
                                    `
                                  : html``}`
                        : html`<ak-form-element-horizontal label=${t`Icon`} name="icon">
                              <input
                                  type="text"
                                  value="${first(this.instance?.metaIcon, "")}"
                                  class="pf-c-form-control"
                              />
                              <p class="pf-c-form__helper-text">
                                  ${t`Either input a full URL, a relative path, or use 'fa://fa-test' to use the Font Awesome icon "fa-test".`}
                              </p>
                          </ak-form-element-horizontal>`}
                    <ak-form-element-horizontal label=${t`Publisher`} name="metaPublisher">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.metaPublisher)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Description`} name="metaDescription">
                        <textarea class="pf-c-form-control">
${ifDefined(this.instance?.metaDescription)}</textarea
                        >
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
