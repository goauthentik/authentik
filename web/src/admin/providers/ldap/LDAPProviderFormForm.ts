import "#admin/common/ak-crypto-certificate-search";
import "#admin/common/ak-flow-search/ak-branded-flow-search";
import "#admin/common/ak-flow-search/ak-flow-search";
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

import {
    CurrentBrand,
    FlowsInstancesListDesignationEnum,
    LDAPProvider,
    ValidationError,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

// All Provider objects have an Authorization flow, but not all providers have an Authentication
// flow. LDAP needs only one field, but it is not an Authorization field, it is an Authentication
// field. So, yeah, we're using the authorization field to store the authentication information,
// which is why the ak-branded-flow-search call down there looks so weird-- we're looking up
// Authentication flows, but we're storing them in the Authorization field of the target Provider.

export function renderForm(
    provider?: Partial<LDAPProvider>,
    errors: ValidationError = {},
    brand?: CurrentBrand,
) {
    return html`
        <ak-text-input
            name="name"
            placeholder=${msg("Provider name")}
            value=${ifDefined(provider?.name)}
            label=${msg("Name")}
            .errorMessages=${errors?.name}
            required
            help=${msg("Method's display Name.")}
        ></ak-text-input>
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
            name="mfaSupport"
            label=${msg("Code-based MFA Support")}
            ?checked=${provider?.mfaSupport ?? true}
            help=${mfaSupportHelp}
        >
        </ak-switch-input>

        <ak-form-group open label="${msg("Flow settings")}">
            <div class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Bind flow")}
                    required
                    name="authorizationFlow"
                    .errorMessages=${errors?.authorizationFlow}
                >
                    <ak-branded-flow-search
                        label=${msg("Bind flow")}
                        flowType=${FlowsInstancesListDesignationEnum.Authentication}
                        .currentFlow=${provider?.authorizationFlow}
                        .brandFlow=${brand?.flowAuthentication}
                        required
                    ></ak-branded-flow-search>
                    <p class="pf-c-form__helper-text">
                        ${msg("Flow used for users to authenticate.")}
                    </p>
                </ak-form-element-horizontal>

                <ak-form-element-horizontal
                    label=${msg("Unbind flow")}
                    name="invalidationFlow"
                    required
                >
                    <ak-branded-flow-search
                        flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                        .currentFlow=${provider?.invalidationFlow}
                        .brandFlow=${brand?.flowInvalidation}
                        defaultFlowSlug="default-invalidation-flow"
                        .errorMessages=${errors?.invalidationFlow}
                        required
                    ></ak-branded-flow-search>
                    <p class="pf-c-form__helper-text">${msg("Flow used for unbinding users.")}</p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group open label="${msg("Protocol settings")}">
            <div class="pf-c-form">
                <ak-text-input
                    name="baseDn"
                    label=${msg("Base DN")}
                    required
                    value="${provider?.baseDn ?? "DC=ldap,DC=goauthentik,DC=io"}"
                    input-hint="code"
                    .errorMessages=${errors?.baseDn}
                    help=${msg(
                        "LDAP DN under which bind requests and search requests can be made.",
                    )}
                >
                </ak-text-input>

                <ak-form-element-horizontal
                    label=${msg("Certificate")}
                    name="certificate"
                    .errorMessages=${errors?.certificate}
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
                    value="${provider?.tlsServerName ?? ""}"
                    .errorMessages=${errors?.tlsServerName}
                    help=${tlsServerNameHelp}
                    input-hint="code"
                ></ak-text-input>

                <ak-number-input
                    label=${msg("UID start number")}
                    required
                    name="uidStartNumber"
                    value="${provider?.uidStartNumber ?? 2000}"
                    .errorMessages=${errors?.uidStartNumber}
                    help=${uidStartNumberHelp}
                ></ak-number-input>

                <ak-number-input
                    label=${msg("GID start number")}
                    required
                    name="gidStartNumber"
                    value="${provider?.gidStartNumber ?? 4000}"
                    .errorMessages=${errors?.gidStartNumber}
                    help=${gidStartNumberHelp}
                ></ak-number-input>
            </div>
        </ak-form-group>
    `;
}
