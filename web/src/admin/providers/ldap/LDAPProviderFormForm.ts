import "#components/ak-switch-input";
import "#components/ak-number-input";
import "#components/ak-radio-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import {
    bindModeOptions,
    cryptoCertificateHelp,
    gidStartNumberHelp,
    mfaSupportHelp,
    searchModeOptions,
    tlsServerNameHelp,
    uidStartNumberHelp,
} from "./LDAPOptionsAndHelp.js";

import { AKCertificateSearch } from "#admin/common/AKCertificateSearch";
import { TLSKeyTypes } from "#admin/common/certificate-key-types";
import {
    AKAuthorizationFlowField,
    AKInvalidationFlowField,
} from "#admin/providers/components/flow-fields";

import { CurrentBrand, FlowDesignationEnum, LDAPProvider, ValidationError } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

// All Provider objects have an Authorization flow, but not all providers have an Authentication
// flow. LDAP needs only one field, but it is not an Authorization field, it is an Authentication
// field. So, yeah, we're using the authorization field to store the authentication information,
// which is why the authorization flow field down there looks so weird-- we're looking up
// Authentication flows, but we're storing them in the Authorization field of the target Provider.

export interface LDAPProviderFormProps {
    provider?: Partial<LDAPProvider> | null;
    errors?: ValidationError;
    brand?: CurrentBrand;
}

export function renderForm({ provider, errors = {}, brand }: LDAPProviderFormProps) {
    provider ||= {};

    return html`
        <ak-text-input
            name="name"
            value=${ifDefined(provider.name)}
            label=${msg("Provider Name")}
            placeholder=${msg("Type a provider name...")}
            spellcheck="false"
            .errorMessages=${errors.name}
            required
        ></ak-text-input>
        <ak-radio-input
            label=${msg("Bind Mode")}
            name="bindMode"
            .options=${bindModeOptions}
            .value=${provider.bindMode}
            help=${msg("Configure how the outpost authenticates requests.")}
        >
        </ak-radio-input>

        <ak-radio-input
            label=${msg("Search Mode")}
            name="searchMode"
            .options=${searchModeOptions}
            .value=${provider.searchMode}
            help=${msg("Configure how the outpost queries the core authentik server's users.")}
        >
        </ak-radio-input>

        <ak-switch-input
            name="mfaSupport"
            label=${msg("Code-based MFA Support")}
            ?checked=${provider.mfaSupport ?? true}
            help=${mfaSupportHelp}
        >
        </ak-switch-input>

        <ak-form-group open label="${msg("Flow settings")}">
            <div class="pf-c-form">
                ${AKAuthorizationFlowField({
                    label: msg("Bind Flow"),
                    placeholder: msg("Select a flow..."),
                    help: msg("Flow used for users to authenticate."),
                    flowType: FlowDesignationEnum.Authentication,
                    value: provider.authorizationFlow,
                    defaultFlowSlug: brand?.flowAuthentication,
                    errors: errors.authorizationFlow,
                })}
                ${AKInvalidationFlowField({
                    label: msg("Unbind Flow"),
                    placeholder: msg("Select a flow..."),
                    help: msg("Flow used for unbinding users."),
                    value: provider.invalidationFlow,
                    defaultFlowSlug: brand?.flowInvalidation ?? "default-invalidation-flow",
                    errors: errors.invalidationFlow,
                })}
            </div>
        </ak-form-group>

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="baseDn"
                    label=${msg("Base DN")}
                    required
                    value="${provider.baseDn ?? "DC=ldap,DC=goauthentik,DC=io"}"
                    input-hint="code"
                    .errorMessages=${errors.baseDn}
                    help=${msg(
                        "LDAP DN under which bind requests and search requests can be made.",
                    )}
                >
                </ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Certificate")}
                    name="certificate"
                    .errorMessages=${errors.certificate}
                >
                    ${AKCertificateSearch({ name: "certificate", label: msg("Certificate"), placeholder: msg("Select a certificate..."), value: provider.certificate, allowedKeyTypes: TLSKeyTypes })}
                    <p class="pf-c-form__helper-text">${cryptoCertificateHelp}</p>
                </ak-form-element-horizontal>

                <ak-text-input
                    label=${msg("TLS Server Name")}
                    name="tlsServerName"
                    value="${provider.tlsServerName ?? ""}"
                    .errorMessages=${errors.tlsServerName}
                    help=${tlsServerNameHelp}
                    input-hint="code"
                ></ak-text-input>

                <ak-number-input
                    label=${msg("UID Start Number")}
                    required
                    name="uidStartNumber"
                    value="${provider.uidStartNumber ?? 2000}"
                    .errorMessages=${errors.uidStartNumber}
                    help=${uidStartNumberHelp}
                ></ak-number-input>

                <ak-number-input
                    label=${msg("GID Start Number")}
                    required
                    name="gidStartNumber"
                    value="${provider.gidStartNumber ?? 4000}"
                    .errorMessages=${errors.gidStartNumber}
                    help=${gidStartNumberHelp}
                ></ak-number-input>
            </div>
        </ak-form-group>
    `;
}
