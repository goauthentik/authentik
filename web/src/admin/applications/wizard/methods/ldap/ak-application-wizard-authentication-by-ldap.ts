import "@goauthentik/admin/applications/wizard/ak-wizard-title";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { WithBrandConfig } from "@goauthentik/elements/Interface/brandProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import { FlowsInstancesListDesignationEnum } from "@goauthentik/api";
import type { LDAPProvider } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";
import {
    bindModeOptions,
    cryptoCertificateHelp,
    gidStartNumberHelp,
    mfaSupportHelp,
    searchModeOptions,
    tlsServerNameHelp,
    uidStartNumberHelp,
} from "./LDAPOptionsAndHelp";

@customElement("ak-application-wizard-authentication-by-ldap")
export class ApplicationWizardApplicationDetails extends WithBrandConfig(BaseProviderPanel) {
    render() {
        const provider = this.wizard.provider as LDAPProvider | undefined;
        const errors = this.wizard.errors.provider;

        return html` <ak-wizard-title>${msg("Configure LDAP Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                <ak-text-input
                    name="name"
                    value=${ifDefined(provider?.name)}
                    label=${msg("Name")}
                    .errorMessages=${errors?.name ?? []}
                    required
                    help=${msg("Method's display Name.")}
                ></ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Bind flow")}
                    ?required=${true}
                    name="authorizationFlow"
                    .errorMessages=${errors?.authorizationFlow ?? []}
                >
                    <ak-branded-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Authentication}
                        .currentFlow=${provider?.authorizationFlow}
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
                    .value=${provider?.bindMode}
                    help=${msg("Configure how the outpost authenticates requests.")}
                >
                </ak-radio-input>

                <ak-radio-input
                    label=${msg("Search mode")}
                    name="searchMode"
                    .options=${searchModeOptions}
                    .value=${provider?.searchMode}
                    help=${msg(
                        "Configure how the outpost queries the core authentik server's users.",
                    )}
                >
                </ak-radio-input>

                <ak-switch-input
                    name="openInNewTab"
                    label=${msg("Code-based MFA Support")}
                    ?checked=${provider?.mfaSupport ?? true}
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
                            value="${first(provider?.baseDn, "DC=ldap,DC=goauthentik,DC=io")}"
                            .errorMessages=${errors?.baseDn ?? []}
                            help=${msg(
                                "LDAP DN under which bind requests and search requests can be made.",
                            )}
                        >
                        </ak-text-input>

                        <ak-form-element-horizontal
                            label=${msg("Certificate")}
                            name="certificate"
                            .errorMessages=${errors?.certificate ?? []}
                        >
                            <ak-crypto-certificate-search
                                certificate=${ifDefined(provider?.certificate ?? nothing)}
                                name="certificate"
                            >
                            </ak-crypto-certificate-search>
                            <p class="pf-c-form__helper-text">${cryptoCertificateHelp}</p>
                        </ak-form-element-horizontal>

                        <ak-text-input
                            label=${msg("TLS Server name")}
                            name="tlsServerName"
                            value="${first(provider?.tlsServerName, "")}"
                            .errorMessages=${errors?.tlsServerName ?? []}
                            help=${tlsServerNameHelp}
                        ></ak-text-input>

                        <ak-number-input
                            label=${msg("UID start number")}
                            required
                            name="uidStartNumber"
                            value="${first(provider?.uidStartNumber, 2000)}"
                            .errorMessages=${errors?.uidStartNumber ?? []}
                            help=${uidStartNumberHelp}
                        ></ak-number-input>

                        <ak-number-input
                            label=${msg("GID start number")}
                            required
                            name="gidStartNumber"
                            value="${first(provider?.gidStartNumber, 4000)}"
                            .errorMessages=${errors?.gidStartNumber ?? []}
                            help=${gidStartNumberHelp}
                        ></ak-number-input>
                    </div>
                </ak-form-group>
            </form>`;
    }
}

export default ApplicationWizardApplicationDetails;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-by-ldap": ApplicationWizardApplicationDetails;
    }
}
