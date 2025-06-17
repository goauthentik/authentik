import "@goauthentik/admin/common/ak-license-notice";
import "@goauthentik/admin/providers/ldap/LDAPProviderForm";
import "@goauthentik/admin/providers/oauth2/OAuth2ProviderForm";
import "@goauthentik/admin/providers/proxy/ProxyProviderForm";
import "@goauthentik/admin/providers/saml/SAMLProviderForm";
import "@goauthentik/admin/providers/saml/SAMLProviderImportForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import "@goauthentik/elements/wizard/TypeCreateWizardPage";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import type { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-provider-wizard")
export class ProviderWizard extends AKElement {
    static styles: CSSResult[] = [PFBase, PFButton];

    @property({ attribute: false })
    public providerTypes: TypeCreate[] = [];

    @property({ attribute: false })
    public finalHandler?: () => Promise<void>;

    @query("ak-wizard")
    private wizard?: Wizard;

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
                .finalHandler=${this.finalHandler}
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
                <button
                    aria-label=${msg("New Provider")}
                    aria-description="${msg("Open the wizard to create a new provider.")}"
                    type="button"
                    slot="trigger"
                    class="pf-c-button pf-m-primary"
                >
                    ${msg("Create")}
                </button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-wizard": ProviderWizard;
    }
}
