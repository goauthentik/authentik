import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, LitElement, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ProvidersApi, TypeCreate } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/wizard/Wizard";
import "../../elements/wizard/WizardPage";
import "./ldap/LDAPProviderForm";
import "./oauth2/OAuth2ProviderForm";
import "./proxy/ProxyProviderForm";
import "./saml/SAMLProviderForm";
import "./saml/SAMLProviderImportForm";

@customElement("ak-provider-wizard")
export class ProviderWizard extends LitElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, AKGlobal, PFRadio];
    }

    @property()
    providerTypes: TypeCreate[] = [];

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
            >
                <ak-wizard-page slot="initial" .sidebarLabel=${() => t`Select type`}>
                    ${this.providerTypes.map((type) => {
                        return html`<div class="pf-c-radio">
                            <input
                                class="pf-c-radio__input"
                                type="radio"
                                name="type"
                                id=${type.component}
                                @change=${() => {
                                    this.dispatchEvent(
                                        new CustomEvent("ak-wizard-set-pages", {
                                            bubbles: true,
                                            composed: true,
                                            detail: ["initial", `type-${type.component}`],
                                        }),
                                    );
                                }}
                            />
                            <label class="pf-c-radio__label" for=${type.component}
                                >${type.name}</label
                            >
                            <span class="pf-c-radio__description">${type.description}</span>
                        </div>`;
                    })}
                </ak-wizard-page>
                ${this.providerTypes.map((type) => {
                    return html`
                        <ak-wizard-page
                            slot=${`type-${type.component}`}
                            .sidebarLabel=${() => t`Create ${type.name}`}
                        >
                            <ak-proxy-form slot="form" type=${type.component}> </ak-proxy-form>
                        </ak-wizard-page>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-wizard>
        `;
    }
}
