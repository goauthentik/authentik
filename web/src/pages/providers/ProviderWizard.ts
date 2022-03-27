import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";

import { FormWizardStep } from "../../elements/wizard/FormWizardStep";
import { Wizard } from "../../elements/wizard/Wizard";
import { WizardStep } from "../../elements/wizard/WizardStep";
import "./ldap/LDAPProviderForm";
import "./oauth2/OAuth2ProviderForm";
import "./proxy/ProxyProviderForm";
import "./saml/SAMLProviderForm";
import "./saml/SAMLProviderImportForm";

export class ProviderInitialStep extends WizardStep {
    selected = false;

    isValid(): boolean {
        return this.selected;
    }

    renderNavList(): TemplateResult {
        return html`${t`Select type`}`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="oauth"
                    @change=${() => {
                        this.host.setSteps(this, new ProviderOAuthDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="oauth">${t`OAuth/OIDC`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a provider which supports OAuth, OIDC or "Login with GitHub
                Enterprise".`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="saml"
                    @change=${() => {
                        this.host.setSteps(this, new ProviderSAMLDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="saml">${t`SAML`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a provider which supports SAML 2.0.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="saml-import"
                    @change=${() => {
                        this.host.setSteps(this, new ProviderSAMLImportDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="saml">${t`SAML (metadata import)`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a provider which supports SAML 2.0, by importing it's metadata.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="ldap"
                    @change=${() => {
                        this.host.setSteps(this, new ProviderLDAPDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="ldap">${t`LDAP`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a provider which support LDAP.`}</span
                >
            </div>
            <div class="pf-c-radio">
                <input
                    class="pf-c-radio__input"
                    type="radio"
                    name="type"
                    id="proxy"
                    @change=${() => {
                        this.host.setSteps(this, new ProviderProxyDetailStep());
                        this.selected = true;
                    }}
                />
                <label class="pf-c-radio__label" for="proxy">${t`Proxy`}</label>
                <span class="pf-c-radio__description"
                    >${t`Add a provider which does not support any other method. Requests will be routed
                through the authentik proxy, which authenticates all requests.`}</span
                >
            </div>`;
    }
}

class ProviderOAuthDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`OAuth details`}`;
    }
    render(): TemplateResult {
        return html`<ak-provider-oauth2-form></ak-provider-oauth2-form>`;
    }
}

class ProviderSAMLDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`SAML details`}`;
    }
    render(): TemplateResult {
        return html`<ak-provider-saml-form></ak-provider-saml-form>`;
    }
}

class ProviderSAMLImportDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`SAML details (import from metadata)`}`;
    }
    render(): TemplateResult {
        return html`<ak-provider-saml-import-form></ak-provider-saml-import-form>`;
    }
}

class ProviderLDAPDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`LDAP details`}`;
    }
    render(): TemplateResult {
        return html`<ak-provider-ldap-form></ak-provider-ldap-form>`;
    }
}

class ProviderProxyDetailStep extends FormWizardStep {
    renderNavList(): TemplateResult {
        return html`${t`Proxy details`}`;
    }
    render(): TemplateResult {
        return html`<ak-provider-proxy-form></ak-provider-proxy-form>`;
    }
}

@customElement("ak-provider-wizard")
export class ProviderWizard extends Wizard {
    header = t`New provider`;
    description = t`Create a new provider.`;

    steps = [new ProviderInitialStep()];

    static get styles(): CSSResult[] {
        return super.styles.concat(PFRadio);
    }
}
