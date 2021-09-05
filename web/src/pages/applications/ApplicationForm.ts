import {
    CoreApi,
    Application,
    ProvidersApi,
    Provider,
    PolicyEngineMode,
    CapabilitiesEnum,
} from "@goauthentik/api";
import { t } from "@lingui/macro";
import { CSSResult, customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { config, DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/buttons/Dropdown";
import "../../elements/Spinner";
import "../../elements/forms/ProxyForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/forms/FormGroup";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import { ModelForm } from "../../elements/forms/ModelForm";
import { first } from "../../utils";

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

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDropdown);
    }

    send = (data: Application): Promise<Application | void> => {
        let writeOp: Promise<Application>;
        if (this.instance) {
            writeOp = new CoreApi(DEFAULT_CONFIG).coreApplicationsUpdate({
                slug: this.instance.slug,
                applicationRequest: data,
            });
        } else {
            writeOp = new CoreApi(DEFAULT_CONFIG).coreApplicationsCreate({
                applicationRequest: data,
            });
        }
        return config().then((c) => {
            if (c.capabilities.includes(CapabilitiesEnum.SaveMedia)) {
                const icon = this.getFormFile();
                if (icon || this.clearIcon) {
                    return writeOp.then((app) => {
                        return new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconCreate({
                            slug: app.slug,
                            file: icon,
                            clear: this.clearIcon,
                        });
                    });
                }
            } else {
                return writeOp.then((app) => {
                    return new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconUrlCreate({
                        slug: app.slug,
                        filePathRequest: {
                            url: data.metaIcon || "",
                        },
                    });
                });
            }
        });
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
                <ak-dropdown class="pf-c-dropdown">
                    <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                        <span class="pf-c-dropdown__toggle-text">${t`Create provider`}</span>
                        <i
                            class="fas fa-caret-down pf-c-dropdown__toggle-icon"
                            aria-hidden="true"
                        ></i>
                    </button>
                    <ul class="pf-c-dropdown__menu" hidden>
                        ${until(
                            new ProvidersApi(DEFAULT_CONFIG)
                                .providersAllTypesList()
                                .then((types) => {
                                    return types.map((type) => {
                                        return html`<li>
                                            <ak-forms-modal>
                                                <span slot="submit"> ${t`Create`} </span>
                                                <span slot="header">
                                                    ${t`Create ${type.name}`}
                                                </span>
                                                <ak-proxy-form slot="form" type=${type.component}>
                                                </ak-proxy-form>
                                                <button
                                                    type="button"
                                                    slot="trigger"
                                                    class="pf-c-dropdown__menu-item"
                                                >
                                                    ${type.name}<br />
                                                    <small>${type.description}</small>
                                                </button>
                                            </ak-forms-modal>
                                        </li>`;
                                    });
                                }),
                            html`<ak-spinner></ak-spinner>`,
                        )}
                    </ul>
                </ak-dropdown>
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
                            </ak-form-element-horizontal>`;
                        }),
                    )}
                    <ak-form-element-horizontal label=${t`Description`} name="metaDescription">
                        <textarea class="pf-c-form-control">
${ifDefined(this.instance?.metaDescription)}</textarea
                        >
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Publisher`} name="metaPublisher">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.metaPublisher)}"
                            class="pf-c-form-control"
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
