import "@goauthentik/admin/common/ak-crypto-certificate-search";
import "@goauthentik/admin/common/ak-flow-search/ak-branded-flow-search";
import "@goauthentik/admin/common/ak-flow-search/ak-flow-search";
import "@goauthentik/components/ak-number-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CurrentBrand,
    FlowsInstancesListDesignationEnum,
    LDAPProvider,
    ValidationError,
} from "@goauthentik/api";

import {
    bindModeOptions,
    cryptoCertificateHelp,
    gidStartNumberHelp,
    mfaSupportHelp,
    searchModeOptions,
    tlsServerNameHelp,
    uidStartNumberHelp,
} from "./LDAPOptionsAndHelp.js";

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
            value=${ifDefined(provider?.name)}
            label=${msg("Name")}
            .errorMessages=${errors?.name ?? []}
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

        <ak-form-group expanded>
            <span slot="header"> ${msg("Flow settings")} </span>

            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal
                    label=${msg("Bind flow")}
                    ?required=${true}
                    name="authorizationFlow"
                    .errorMessages=${errors?.authorizationFlow ?? []}
                >
                    <ak-branded-flow-search
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
                        .errorMessages=${errors?.invalidationFlow ?? []}
                        required
                    ></ak-branded-flow-search>
                    <p class="pf-c-form__helper-text">${msg("Flow used for unbinding users.")}</p>
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>

        <ak-form-group expanded>
            <span slot="header"> ${msg("Protocol settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-text-input
                    name="baseDn"
                    label=${msg("Base DN")}
                    required
                    value="${provider?.baseDn ?? "DC=ldap,DC=goauthentik,DC=io"}"
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
                    value="${provider?.tlsServerName ?? ""}"
                    .errorMessages=${errors?.tlsServerName ?? []}
                    help=${tlsServerNameHelp}
                ></ak-text-input>

                <ak-number-input
                    label=${msg("UID start number")}
                    required
                    name="uidStartNumber"
                    value="${provider?.uidStartNumber ?? 2000}"
                    .errorMessages=${errors?.uidStartNumber ?? []}
                    help=${uidStartNumberHelp}
                ></ak-number-input>

                <ak-number-input
                    label=${msg("GID start number")}
                    required
                    name="gidStartNumber"
                    value="${provider?.gidStartNumber ?? 4000}"
                    .errorMessages=${errors?.gidStartNumber ?? []}
                    help=${gidStartNumberHelp}
                ></ak-number-input>
            </div>
        </ak-form-group>
    `;
}
