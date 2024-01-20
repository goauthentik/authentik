import "@goauthentik/admin/providers/ldap/LDAPProviderForm.js";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm.js";
import "@goauthentik/admin/providers/proxy/ProxyProviderForm.js";
import "@goauthentik/admin/providers/saml/SAMLProviderForm.js";
import "@goauthentik/admin/providers/saml/SAMLProviderImportForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import "@goauthentik/elements/Alert.js";
import { AKElement } from "@goauthentik/elements/Base.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import { paramURL } from "@goauthentik/elements/router/RouterOutlet.js";
import "@goauthentik/elements/wizard/FormWizardPage.js";
import "@goauthentik/elements/wizard/Wizard.js";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage.js";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFHint from "@patternfly/patternfly/components/Hint/hint.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EnterpriseApi, LicenseSummary, ProvidersApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-provider-wizard-initial")
export class InitialProviderWizardPage extends WizardPage {
    @property({ attribute: false })
    providerTypes: TypeCreate[] = [];

    @property({ attribute: false })
    enterprise?: LicenseSummary;

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFHint, PFButton, PFRadio];
    }
    sidebarLabel = () => msg("Select type");

    activeCallback: () => Promise<void> = async () => {
        this.host.isValid = false;
        this.shadowRoot
            ?.querySelectorAll<HTMLInputElement>("input[type=radio]")
            .forEach((radio) => {
                if (radio.checked) {
                    radio.dispatchEvent(new CustomEvent("change"));
                }
            });
    };

    renderHint(): TemplateResult {
        return html`<div class="pf-c-hint">
                <div class="pf-c-hint__title">${msg("Try the new application wizard")}</div>
                <div class="pf-c-hint__body">
                    ${msg(
                        "The new application wizard greatly simplifies the steps required to create applications and providers.",
                    )}
                </div>
                <div class="pf-c-hint__footer">
                    <a
                        class="pf-c-button pf-m-link pf-m-inline"
                        href=${paramURL("/core/applications", {
                            createForm: true,
                        })}
                        >${msg("Try it now")}</a
                    >
                </div>
            </div>
            <br />`;
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.providerTypes.map((type) => {
                return html`<div class="pf-c-radio">
                    <input
                        class="pf-c-radio__input"
                        type="radio"
                        name="type"
                        id=${type.component}
                        @change=${() => {
                            this.host.steps = ["initial", `type-${type.component}`];
                            this.host.isValid = true;
                        }}
                        ?disabled=${type.requiresEnterprise ? !this.enterprise?.hasLicense : false}
                    />
                    <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
                    <span class="pf-c-radio__description">${type.description}</span>
                    ${type.requiresEnterprise && !this.enterprise?.hasLicense
                        ? html`
                              <ak-alert class="pf-c-radio__description" ?inline=${true}>
                                  ${msg("Provider require enterprise.")}
                                  <a href="#/enterprise/licenses">${msg("Learn more")}</a>
                              </ak-alert>
                          `
                        : nothing}
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-provider-wizard")
export class ProviderWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFRadio];
    }

    @property()
    createText = msg("Create");

    @property({ attribute: false })
    providerTypes: TypeCreate[] = [];

    @state()
    enterprise?: LicenseSummary;

    @property({ attribute: false })
    finalHandler: () => Promise<void> = () => {
        return Promise.resolve();
    };

    async firstUpdated(): Promise<void> {
        this.providerTypes = await new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList();
        this.enterprise = await new EnterpriseApi(
            DEFAULT_CONFIG,
        ).enterpriseLicenseSummaryRetrieve();
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${msg("New provider")}
                description=${msg("Create a new provider.")}
                .finalHandler=${() => {
                    return this.finalHandler();
                }}
            >
                <ak-provider-wizard-initial
                    slot="initial"
                    .providerTypes=${this.providerTypes}
                    .enterprise=${this.enterprise}
                >
                </ak-provider-wizard-initial>
                ${this.providerTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}`}
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form type=${type.component}></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${this.createText}</button>
            </ak-wizard>
        `;
    }
}
