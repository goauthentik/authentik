import "@goauthentik/admin/providers/ProviderWizard";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/ProxyForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    Application,
    CapabilitiesEnum,
    CoreApi,
    PolicyEngineMode,
    Provider,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-application-form")
export class ApplicationForm extends ModelForm<Application, string> {
    loadInstance(pk: string): Promise<Application> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsRetrieve({
            slug: pk,
        });
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

    send = async (data: Application): Promise<Application | void> => {
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
        if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
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
    };

    groupProviders(providers: Provider[]): TemplateResult {
        const m = new Map<string, Provider[]>();
        providers.forEach((p) => {
            if (!m.has(p.verboseName || "")) {
                m.set(p.verboseName || "", []);
            }
            const tProviders = m.get(p.verboseName || "") || [];
            tProviders.push(p);
        });
        return html`
            ${Array.from(m).map(([group, providers]) => {
                return html`<optgroup label=${group}>
                    ${providers.map((p) => {
                        const selected = this.instance?.provider === p.pk || this.provider === p.pk;
                        return html`<option ?selected=${selected} value=${ifDefined(p.pk)}>
                            ${p.name}
                        </option>`;
                    })}
                </optgroup>`;
            })}
        `;
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
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.provider === undefined}>
                        ---------
                    </option>
                    ${until(
                        new ProvidersApi(DEFAULT_CONFIG).providersAllList({}).then((providers) => {
                            return this.groupProviders(providers.results);
                        }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Select a provider that this application should use. Alternatively, create a new provider.`}
                </p>
                <ak-provider-wizard
                    .finalHandler=${async () => {
                        this.requestUpdate();
                    }}
                    createText=${t`Create provider`}
                >
                </ak-provider-wizard>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Policy engine mode`}
                ?required=${true}
                name="policyEngineMode"
            >
                <select class="pf-c-form-control">
                    <option
                        value=${PolicyEngineMode.Any}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.Any}
                    >
                        ${t`ANY, any policy must match to grant access.`}
                    </option>
                    <option
                        value=${PolicyEngineMode.All}
                        ?selected=${this.instance?.policyEngineMode === PolicyEngineMode.All}
                    >
                        ${t`ALL, all policies must match to grant access.`}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
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
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.openInNewTab, false)}
                            />
                            <label class="pf-c-check__label"> ${t`Open in new tab`} </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${t`If checked, the launch URL will open in a new browser tab or window from the user's application library.`}
                        </p>
                    </ak-form-element-horizontal>
                    ${until(
                        config().then((c) => {
                            if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                                return html`<ak-form-element-horizontal
                                        label=${t`Icon`}
                                        name="metaIcon"
                                    >
                                        <input type="file" value="" class="pf-c-form-control" />
                                        ${this.instance?.metaIcon
                                            ? html`
                                                  <p class="pf-c-form__helper-text">
                                                      ${t`Currently set to:`}
                                                      ${this.instance?.metaIcon}
                                                  </p>
                                              `
                                            : html``}
                                    </ak-form-element-horizontal>
                                    ${this.instance?.metaIcon
                                        ? html`
                                              <ak-form-element-horizontal>
                                                  <div class="pf-c-check">
                                                      <input
                                                          type="checkbox"
                                                          class="pf-c-check__input"
                                                          @change=${(ev: Event) => {
                                                              const target =
                                                                  ev.target as HTMLInputElement;
                                                              this.clearIcon = target.checked;
                                                          }}
                                                      />
                                                      <label class="pf-c-check__label">
                                                          ${t`Clear icon`}
                                                      </label>
                                                  </div>
                                                  <p class="pf-c-form__helper-text">
                                                      ${t`Delete currently set icon.`}
                                                  </p>
                                              </ak-form-element-horizontal>
                                          `
                                        : html``}`;
                            }
                            return html`<ak-form-element-horizontal
                                label=${t`Icon`}
                                name="metaIcon"
                            >
                                <input
                                    type="text"
                                    value="${first(this.instance?.metaIcon, "")}"
                                    class="pf-c-form-control"
                                />
                                <p class="pf-c-form__helper-text">
                                    ${t`Either input a full URL, a relative path, or use 'fa://fa-test' to use the Font Awesome icon "fa-test".`}
                                </p>
                            </ak-form-element-horizontal>`;
                        }),
                    )}
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
