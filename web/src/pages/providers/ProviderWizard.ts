import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/forms/ProxyForm";
import { paramURL } from "@goauthentik/web/elements/router/RouterOutlet";
import "@goauthentik/web/elements/wizard/FormWizardPage";
import "@goauthentik/web/elements/wizard/Wizard";
import { WizardPage } from "@goauthentik/web/elements/wizard/WizardPage";
import "@goauthentik/web/pages/providers/ldap/LDAPProviderForm";
import "@goauthentik/web/pages/providers/oauth2/OAuth2ProviderForm";
import "@goauthentik/web/pages/providers/proxy/ProxyProviderForm";
import "@goauthentik/web/pages/providers/saml/SAMLProviderForm";
import "@goauthentik/web/pages/providers/saml/SAMLProviderImportForm";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/web/authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFHint from "@patternfly/patternfly/components/Hint/hint.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-provider-wizard-initial")
export class InitialProviderWizardPage extends WizardPage {
    @property({ attribute: false })
    providerTypes: TypeCreate[] = [];

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFHint, PFButton, AKGlobal, PFRadio];
    }
    sidebarLabel = () => t`Select type`;

    renderHint(): TemplateResult {
        return html`<div class="pf-c-hint">
                <div class="pf-c-hint__title">${t`Try the new application wizard`}</div>
                <div class="pf-c-hint__body">
                    ${t`The new application wizard greatly simplifies the steps required to create applications and providers.`}
                </div>
                <div class="pf-c-hint__footer">
                    <a
                        class="pf-c-button pf-m-link pf-m-inline"
                        href=${paramURL("/core/applications", {
                            createForm: true,
                        })}
                        >${t`Try it now`}</a
                    >
                </div>
            </div>
            <br />`;
    }

    render(): TemplateResult {
        return html` <form class="pf-c-form pf-m-horizontal">
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
                    />
                    <label class="pf-c-radio__label" for=${type.component}>${type.name}</label>
                    <span class="pf-c-radio__description">${type.description}</span>
                </div>`;
            })}
        </form>`;
    }
}

@customElement("ak-provider-wizard")
export class ProviderWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property()
    createText = t`Create`;

    @property({ attribute: false })
    providerTypes: TypeCreate[] = [];

    @property({ attribute: false })
    finalHandler: () => Promise<void> = () => {
        return Promise.resolve();
    };

    firstUpdated(): void {
        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((types) => {
            this.providerTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${t`New provider`}
                description=${t`Create a new provider.`}
                .finalHandler=${() => {
                    return this.finalHandler();
                }}
            >
                <ak-provider-wizard-initial slot="initial" .providerTypes=${this.providerTypes}>
                </ak-provider-wizard-initial>
                ${this.providerTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
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
