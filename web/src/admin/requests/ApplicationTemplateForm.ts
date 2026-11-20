import "#components/ak-text-input";
import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { AKCertificateSearch } from "#admin/common/AKCertificateSearch";
import { JWTSigningKeyTypes } from "#admin/common/certificate-key-types";
import {
    AKAuthorizationFlowField,
    AKInvalidationFlowField,
} from "#admin/providers/components/flow-fields";
import { GrantTypeCheckboxItems } from "#admin/providers/oauth2/labels";
import {
    propertyMappingsProvider,
    propertyMappingsSelector,
} from "#admin/providers/oauth2/OAuth2ProviderFormHelpers";
import { groupsProvider, groupsSelector } from "#admin/providers/scim/SCIMProviderFormHelpers";

import { ApplicationTemplate, GrantTypeEnum, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-template-form")
export class ApplicationTemplateForm extends ModelForm<ApplicationTemplate, string> {
    public static override verboseName = msg("Application Template", {
        id: "requests.application-template.verbose-name",
    });
    public static override verboseNamePlural = msg("Application Templates", {
        id: "requests.application-template.verbose-name-plural",
    });

    protected async loadInstance(pk: string): Promise<ApplicationTemplate> {
        return aki(RequestsApi).requestsApplicationTemplatesRetrieve({ uuid: pk });
    }

    protected override async send(data: ApplicationTemplate): Promise<ApplicationTemplate> {
        if (this.instance?.uuid) {
            return aki(RequestsApi).requestsApplicationTemplatesUpdate({
                uuid: this.instance.uuid,
                applicationTemplateRequest: data,
            });
        }

        return aki(RequestsApi).requestsApplicationTemplatesCreate({
            applicationTemplateRequest: data,
        });
    }

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Name", { id: "requests.application-template.name.label" })}
                name="name"
                required
                value=${ifDefined(this.instance?.name)}
                help=${msg("Shown to requesters on the Discover page.", {
                    id: "requests.application-template.name.help",
                })}
            ></ak-text-input>
            ${AKAuthorizationFlowField({
                value: this.instance?.authorizationFlow,
                help: msg("Authorization flow of every provider created from this template.", {
                    id: "requests.application-template.authorization-flow.help",
                }),
            })}
            ${AKInvalidationFlowField({
                value: this.instance?.invalidationFlow,
                help: msg("Invalidation flow of every provider created from this template.", {
                    id: "requests.application-template.invalidation-flow.help",
                }),
            })}
            <ak-form-element-horizontal
                label=${msg("Scopes", { id: "requests.application-template.scopes.label" })}
                name="propertyMappings"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${propertyMappingsProvider}
                    .selector=${propertyMappingsSelector(this.instance?.propertyMappings)}
                    available-label=${msg("Available Scopes")}
                    selected-label=${msg("Selected Scopes")}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Scope mappings of every provider created from this template. Leave out mappings such as authentik API access, which give the application more than information about the user.",
                        { id: "requests.application-template.scopes.help" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Signing Key", {
                    id: "requests.application-template.signing-key.label",
                })}
                name="signingKey"
            >
                ${AKCertificateSearch({
                    name: "signingKey",
                    label: msg("Signing Key", {
                        id: "requests.application-template.signing-key.label",
                    }),
                    placeholder: msg("Select a signing key...", {
                        id: "requests.application-template.signing-key.placeholder",
                    }),
                    value: this.instance?.signingKey,
                    allowedKeyTypes: JWTSigningKeyTypes,
                })}
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If no signing key is selected, tokens are signed with HS256 using each provider's client secret.",
                        { id: "requests.application-template.signing-key.help" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Allowed grant types", {
                    id: "requests.application-template.allowed-grant-types.label",
                })}
                required
                name="allowedGrantTypes"
            >
                <ak-checkbox-group
                    name="allowedGrantTypes"
                    .options=${GrantTypeCheckboxItems}
                    .value=${this.instance?.allowedGrantTypes ?? [GrantTypeEnum.AuthorizationCode]}
                ></ak-checkbox-group>
                <p class="pf-c-form__helper-text">
                    ${msg("Grant types a requester can choose from.", {
                        id: "requests.application-template.allowed-grant-types.help",
                    })}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Bindable groups", {
                    id: "requests.application-template.bindable-groups.label",
                })}
                required
                name="bindableGroups"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${groupsProvider}
                    .selector=${groupsSelector(this.instance?.bindableGroups)}
                    available-label=${msg("Available groups", {
                        id: "requests.application-template.bindable-groups.available",
                    })}
                    selected-label=${msg("Bindable groups", {
                        id: "requests.application-template.bindable-groups.label",
                    })}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Groups a requester can give access to the new application. Requesters choose at least one.",
                        { id: "requests.application-template.bindable-groups.help" },
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-text-input
                label=${msg("Application group", {
                    id: "requests.application-template.application-group.label",
                })}
                name="applicationGroup"
                value=${ifDefined(this.instance?.applicationGroup)}
                help=${msg("Group that created applications are shown under in the library.", {
                    id: "requests.application-template.application-group.help",
                })}
            ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-template-form": ApplicationTemplateForm;
    }
}
