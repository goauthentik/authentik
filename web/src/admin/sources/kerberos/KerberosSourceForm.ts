import "@goauthentik/admin/common/ak-crypto-certificate-search";
import { placeholderHelperText } from "@goauthentik/admin/helperText";
import { BaseSourceForm } from "@goauthentik/admin/sources/BaseSourceForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-dynamic-selected-provider.js";
import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types.js";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    KerberosSource,
    KerberosSourcePropertyMapping,
    KerberosSourceRequest,
    PropertymappingsApi,
    SourcesApi,
} from "@goauthentik/api";

async function propertyMappingsProvider(page = 1, search = "") {
    const propertyMappings = await new PropertymappingsApi(
        DEFAULT_CONFIG,
    ).propertymappingsSourceKerberosList({
        ordering: "managed",
        pageSize: 20,
        search: search.trim(),
        page,
    });

    return {
        pagination: propertyMappings.pagination,
        options: propertyMappings.results.map((m) => [m.pk, m.name, m.name, m]),
    };
}

function makePropertyMappingsSelector(instanceMappings?: string[]) {
    const localMappings = instanceMappings ? new Set(instanceMappings) : undefined;
    return localMappings
        ? ([pk, _]: DualSelectPair) => localMappings.has(pk)
        : ([_0, _1, _2, _mapping]: DualSelectPair<KerberosSourcePropertyMapping>) => false;
}

@customElement("ak-source-kerberos-form")
export class KerberosSourceForm extends BaseSourceForm<KerberosSource> {
    loadInstance(pk: string): Promise<KerberosSource> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosRetrieve({
            slug: pk,
        });
    }

    async send(data: KerberosSource): Promise<KerberosSource> {
        if (this.instance) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosPartialUpdate({
                slug: this.instance.slug,
                patchedKerberosSourceRequest: data,
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesKerberosCreate({
                kerberosSourceRequest: data as unknown as KerberosSourceRequest,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Slug")} ?required=${true} name="slug">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.slug)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.enabled, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Enabled")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="passwordLoginUpdateInternalPassword">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.passwordLoginUpdateInternalPassword, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Update internal password on login")}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When the user logs in to authentik using this source password backend, update their credentials in authentik.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsers">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.syncUsers, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Sync users")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsersPassword">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.syncUsersPassword, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("User password writeback")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Login password is synced from Kerberos into authentik automatically. Enable this option only to write password changes in authentik back to Kerberos.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Connection settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Realm")}
                        ?required=${true}
                        name="realm"
                    >
                        <input
                            type="text"
                            placeholder="AUTHENTIK.COMPANY"
                            value="${ifDefined(this.instance?.realm)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">${msg("Realm of the KDC")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Kerberos 5 configuration")}
                        name="krb5Conf"
                    >
                        <input
                            type="textarea"
                            value="${ifDefined(this.instance?.krb5Conf)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Kerberos 5 configuration. See man krb5.conf(5) for configuration format. If left empty, a default krb5.conf will be used.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Sync principal")} name="syncPrincipal">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.syncPrincipal)}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Principal used to authenticate to the KDC for syncing. Optional if Sync keytab or Sync credentials cache is provided.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Sync Password")}
                        ?writeOnly=${this.instance !== undefined}
                        name="syncPassword"
                    >
                        <input type="text" value="" class="pf-c-form-control" />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Password used to authenticate to the KDC for syncing. Optional if Sync keytab or Sync credentials cache is provided.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Sync keytab")}
                        ?writeOnly=${this.instance !== undefined}
                        name="syncKeytab"
                    >
                        <input type="text" value="" class="pf-c-form-control" />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Keytab used to authenticate to the KDC for syncing. Optional if Sync principal/password or Sync credentials cache is provided. Must be base64 encoded or in the form TYPE:residual.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Sync credentials cache")}
                        name="syncCcache"
                    >
                        <input type="text" value="" class="pf-c-form-control" />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Credentials cache used to authenticate to the KDC for syncing. Optional if Sync principal/password or Sync keytab is provided. Must be in the form TYPE:residual.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group ?expanded=${true}>
                <span slot="header"> ${msg("Kerberos Attribute mapping")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User Property Mappings")}
                        name="userPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${makePropertyMappingsSelector(
                                this.instance?.userPropertyMappings,
                            )}
                            available-label="${msg("Available User Property Mappings")}"
                            selected-label="${msg("Selected User Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for user creation.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Group Property Mappings")}
                        name="groupPropertyMappings"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${propertyMappingsProvider}
                            .selector=${makePropertyMappingsSelector(
                                this.instance?.groupPropertyMappings,
                            )}
                            available-label="${msg("Available Group Property Mappings")}"
                            selected-label="${msg("Selected Group Property Mappings")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg("Property mappings for group creation.")}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header"> ${msg("Additional settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("User path")} name="userPathTemplate">
                        <input
                            type="text"
                            value="${first(
                                this.instance?.userPathTemplate,
                                "goauthentik.io/sources/%(slug)s",
                            )}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">${placeholderHelperText}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-kerberos-form": KerberosSourceForm;
    }
}
