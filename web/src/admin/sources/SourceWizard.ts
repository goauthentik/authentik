import "@goauthentik/admin/sources/kerberos/KerberosSourceForm";
import "@goauthentik/admin/sources/ldap/LDAPSourceForm";
import "@goauthentik/admin/sources/oauth/OAuthSourceForm";
import "@goauthentik/admin/sources/plex/PlexSourceForm";
import "@goauthentik/admin/sources/saml/SAMLSourceForm";
import "@goauthentik/admin/sources/scim/SCIMSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/wizard/FormWizardPage";
import { TypeCreateWizardPageLayouts } from "@goauthentik/elements/wizard/TypeCreateWizardPage";
import "@goauthentik/elements/wizard/Wizard";
import type { Wizard } from "@goauthentik/elements/wizard/Wizard";

import { msg, str } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property, query } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { SourcesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-source-wizard")
export class SourceWizard extends AKElement {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton];
    }

    @property({ attribute: false })
    sourceTypes: TypeCreate[] = [];

    @query("ak-wizard")
    wizard?: Wizard;

    firstUpdated(): void {
        new SourcesApi(DEFAULT_CONFIG).sourcesAllTypesList().then((types) => {
            this.sourceTypes = types;
        });
    }

    render(): TemplateResult {
        return html`
            <ak-wizard
                .steps=${["initial"]}
                header=${msg("New source")}
                description=${msg("Create a new source.")}
            >
                <ak-wizard-page-type-create
                    slot="initial"
                    .types=${this.sourceTypes}
                    layout=${TypeCreateWizardPageLayouts.grid}
                    @select=${(ev: CustomEvent<TypeCreate>) => {
                        if (!this.wizard) return;
                        this.wizard.steps = [
                            "initial",
                            `type-${ev.detail.component}-${ev.detail.modelName}`,
                        ];
                        this.wizard.isValid = true;
                    }}
                >
                </ak-wizard-page-type-create>
                ${this.sourceTypes.map((type) => {
                    return html`
                        <ak-wizard-page-form
                            slot=${`type-${type.component}-${type.modelName}`}
                            .sidebarLabel=${() => msg(str`Create ${type.name}`)}
                        >
                            <ak-proxy-form
                                .args=${{
                                    modelName: type.modelName,
                                }}
                                type=${type.component}
                            ></ak-proxy-form>
                        </ak-wizard-page-form>
                    `;
                })}
                <button slot="trigger" class="pf-c-button pf-m-primary">${msg("Create")}</button>
            </ak-wizard>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-wizard": SourceWizard;
    }
}
