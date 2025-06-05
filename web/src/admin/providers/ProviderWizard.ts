import "#elements/forms/ProxyForm";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";
import "#admin/common/ak-license-notice";
import "#admin/providers/ldap/LDAPProviderForm";
import "#admin/providers/oauth2/OAuth2ProviderForm";
import "#admin/providers/proxy/ProxyProviderForm";
import "#admin/providers/saml/SAMLProviderForm";
import "#admin/providers/saml/SAMLProviderImportForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";
import type { Wizard } from "#elements/wizard/Wizard";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-provider-wizard")
export class ProviderWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property()
    createText = msg("Create");

    @property({ attribute: false })
    providerTypes: TypeCreate[] = [];

    @property({ attribute: false })
    finalHandler: () => Promise<void> = () => {
        return Promise.resolve();
    };

    @query("ak-wizard")
    wizard?: Wizard;

    connectedCallback() {
        super.connectedCallback();
        new ProvidersApi(DEFAULT_CONFIG).providersAllTypesList().then((providerTypes) => {
            this.providerTypes = providerTypes;
        });
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
                <ak-wizard-page-type-create
                    name="selectProviderType"
                    slot="initial"
                    layout=${TypeCreateWizardPageLayouts.grid}
                    .types=${this.providerTypes}
                    @select=${(ev: CustomEvent<TypeCreate>) => {
                        if (!this.wizard) return;
                        this.wizard.steps = ["initial", `type-${ev.detail.component}`];
                        this.wizard.isValid = true;
                    }}
                >
                </ak-wizard-page-type-create>
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wizard": ProviderWizard;
    }
}
