import "@goauthentik/admin/common/ak-core-group-search";
import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-tenanted-flow-search";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { rootInterface } from "@goauthentik/elements/Base";
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
    groupHelp,
    mfaSupportHelp,
    searchModeOptions,
    tlsServerNameHelp,
    uidStartNumberHelp,
} from "./LDAPOptionsAndHelp";

@customElement("ak-application-wizard-authentication-by-ldap")
export class ApplicationWizardApplicationDetails extends BaseProviderPanel {
    render() {
        const provider = this.wizard.provider as LDAPProvider | undefined;

        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${ifDefined(provider?.name)}
                label=${msg("Name")}
                required
                help=${msg("Method's display Name.")}
            ></ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Bind flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-tenanted-flow-search
                    flowType=${FlowsInstancesListDesignationEnum.Authentication}
                    .currentFlow=${provider?.authorizationFlow}
                    .tenantFlow=${rootInterface()?.tenant?.flowAuthentication}
                    required
                ></ak-tenanted-flow-search>
                <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Search group")} name="searchGroup">
                <ak-core-group-search
                    name="searchGroup"
                    group=${ifDefined(provider?.searchGroup ?? nothing)}
                ></ak-core-group-search>
                <p class="pf-c-form__helper-text">${groupHelp}</p>
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
                help=${msg("Configure how the outpost queries the core authentik server's users.")}
            >
            </ak-radio-input>

            <ak-switch-input
                name="openInNewTab"
                label=${msg("Code-based MFA Support")}
                ?checked=${provider?.mfaSupport}
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
                        help=${msg(
                            "LDAP DN under which bind requests and search requests can be made.",
                        )}
                    >
                    </ak-text-input>

                    <ak-form-element-horizontal label=${msg("Certificate")} name="certificate">
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
                        help=${tlsServerNameHelp}
                    ></ak-text-input>

                    <ak-number-input
                        label=${msg("UID start number")}
                        required
                        name="uidStartNumber"
                        value="${first(provider?.uidStartNumber, 2000)}"
                        help=${uidStartNumberHelp}
                    ></ak-number-input>

                    <ak-number-input
                        label=${msg("GID start number")}
                        required
                        name="gidStartNumber"
                        value="${first(provider?.gidStartNumber, 4000)}"
                        help=${gidStartNumberHelp}
                    ></ak-number-input>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardApplicationDetails;
