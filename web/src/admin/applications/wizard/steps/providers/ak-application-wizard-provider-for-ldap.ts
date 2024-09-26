import "@goauthentik/admin/common/ak-crypto-certificate-search.js";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search.js";
import { first } from "@goauthentik/common/utils.js";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider.js";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum } from "@goauthentik/api";
import type { LDAPProvider } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";
import {
    bindModeOptions,
    cryptoCertificateHelp,
    gidStartNumberHelp,
    mfaSupportHelp,
    searchModeOptions,
    tlsServerNameHelp,
    uidStartNumberHelp,
} from "./LDAPProviderOptionsAndHelp.js";

@customElement("ak-application-wizard-provider-for-ldap")
export class ApplicationWizardLdapProviderForm extends WithBrandConfig(
    ApplicationWizardProviderForm<LDAPProvider>,
) {
    label = msg("Configure LDAP");

    renderForm(provider: LDAPProvider) {
        return html`
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    value=${ifDefined(provider.name)}
                    label=${msg("Name")}
                    .errorMessages=${this.errorMessages("name")}
                    required
                    help=${msg("Method's display Name.")}
                ></ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Bind flow")}
                    ?required=${true}
                    name="authorizationFlow"
                    .errorMessages=${this.errorMessages("authorization_flow")}
                >
                    <ak-branded-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authentication}
                        .currentFlow=${provider.authorizationFlow}
                        .brandFlow=${this.brand.flowAuthentication}
                        required
                    ></ak-branded-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used for users to authenticate.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-radio-input
                    label=${msg("Bind mode")}
                    name="bindMode"
                    .options=${bindModeOptions}
                    .value=${provider.bindMode}
                    help=${msg("Configure how the outpost authenticates requests.")}
                >
                </ak-radio-input>

                <ak-radio-input
                    label=${msg("Search mode")}
                    name="searchMode"
                    .options=${searchModeOptions}
                    .value=${provider.searchMode}
                    help=${msg(
                        "Configure how the outpost queries the core authentik server's users.",
                    )}
                >
                </ak-radio-input>

                <ak-switch-input
                    name="openInNewTab"
                    label=${msg("Code-based MFA Support")}
                    ?checked=${provider.mfaSupport ?? true}
                    help=${mfaSupportHelp}
                >
                </ak-switch-input>

                <ak-form-group .expanded=${true}>
                    <span slot="header"> ${msg("Protocol settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-text-input
                            name="baseDn"
                            label=${msg("Base DN")}
                            required
                            value="${first(provider.baseDn, "DC=ldap,DC=goauthentik,DC=io")}"
                            .errorMessages=${this.errorMessages("baseDn")}
                            help=${msg(
                                "LDAP DN under which bind requests and search requests can be made.",
                            )}
                        >
                        </ak-text-input>

                        <ak-form-element-horizontal
                            label=${msg("Certificate")}
                            name="certificate"
                            .errorMessages=${this.errorMessages("certificate")}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(provider.certificate ?? nothing)}
                                name="certificate"
                            >
                            </ak-crypto-certificate-search>
                            <p class="pf-c-form__helper-text">${cryptoCertificateHelp}</p>
                        </ak-form-element-horizontal>

                        <ak-text-input
                            label=${msg("TLS Server name")}
                            name="tlsServerName"
                            value="${first(provider.tlsServerName, "")}"
                            .errorMessages=${this.errorMessages("tlsServerName")}
                            help=${tlsServerNameHelp}
                        ></ak-text-input>

                        <ak-number-input
                            label=${msg("UID start number")}
                            required
                            name="uidStartNumber"
                            value="${first(provider.uidStartNumber, 2000)}"
                            .errorMessages=${this.errorMessages("uidStartNumber")}
                            help=${uidStartNumberHelp}
                        ></ak-number-input>

                        <ak-number-input
                            label=${msg("GID start number")}
                            required
                            name="gidStartNumber"
                            value="${first(provider.gidStartNumber, 4000)}"
                            .errorMessages=${this.errorMessages("gidStartNumber")}
                            help=${gidStartNumberHelp}
                        ></ak-number-input>
                    </div>
                </ak-form-group>
            </form>
        `;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("LDAP Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as LDAPProvider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-ldap": ApplicationWizardLdapProviderForm;
    }
}
