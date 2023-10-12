import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    Outpost,
    OutpostDefaultConfig,
    OutpostTypeEnum,
    OutpostsApi,
    OutpostsServiceConnectionsAllListRequest,
    PaginatedLDAPProviderList,
    PaginatedProxyProviderList,
    PaginatedRadiusProviderList,
    ProvidersApi,
    ServiceConnection,
} from "@goauthentik/api";

@customElement("ak-outpost-form")
export class OutpostForm extends ModelForm<Outpost, string> {
    @property()
    type: OutpostTypeEnum = OutpostTypeEnum.Proxy;

    @property({ type: Boolean })
    embedded = false;

    @state()
    providers?:
        | PaginatedProxyProviderList
        | PaginatedLDAPProviderList
        | PaginatedRadiusProviderList;

    defaultConfig?: OutpostDefaultConfig;

    async loadInstance(pk: string): Promise<Outpost> {
        const o = await new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesRetrieve({
            uuid: pk,
        });
        this.type = o.type || OutpostTypeEnum.Proxy;
        return o;
    }

    async load(): Promise<void> {
        this.defaultConfig = await new OutpostsApi(
            DEFAULT_CONFIG,
        ).outpostsInstancesDefaultSettingsRetrieve();
        switch (this.type) {
            case OutpostTypeEnum.Proxy:
                this.providers = await new ProvidersApi(DEFAULT_CONFIG).providersProxyList({
                    ordering: "name",
                    applicationIsnull: false,
                });
                break;
            case OutpostTypeEnum.Ldap:
                this.providers = await new ProvidersApi(DEFAULT_CONFIG).providersLdapList({
                    ordering: "name",
                    applicationIsnull: false,
                });
                break;
            case OutpostTypeEnum.Radius:
                this.providers = await new ProvidersApi(DEFAULT_CONFIG).providersRadiusList({
                    ordering: "name",
                    applicationIsnull: false,
                });
                break;
            case OutpostTypeEnum.UnknownDefaultOpenApi:
                this.providers = undefined;
        }
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated outpost.");
        } else {
            return msg("Successfully created outpost.");
        }
    }

    async send(data: Outpost): Promise<Outpost> {
        if (this.instance) {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesUpdate({
                uuid: this.instance.pk || "",
                outpostRequest: data,
            });
        } else {
            return new OutpostsApi(DEFAULT_CONFIG).outpostsInstancesCreate({
                outpostRequest: data,
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
            <ak-form-element-horizontal label=${msg("Type")} ?required=${true} name="type">
                <select
                    class="pf-c-form-control"
                    @change=${(ev: Event) => {
                        const target = ev.target as HTMLSelectElement;
                        this.type = target.selectedOptions[0].value as OutpostTypeEnum;
                        this.load();
                    }}
                >
                    <option
                        value=${OutpostTypeEnum.Proxy}
                        ?selected=${this.instance?.type === OutpostTypeEnum.Proxy}
                    >
                        ${msg("Proxy")}
                    </option>
                    <option
                        value=${OutpostTypeEnum.Ldap}
                        ?selected=${this.instance?.type === OutpostTypeEnum.Ldap}
                    >
                        ${msg("LDAP")}
                    </option>
                    <option
                        value=${OutpostTypeEnum.Radius}
                        ?selected=${this.instance?.type === OutpostTypeEnum.Radius}
                    >
                        ${msg("Radius")}
                    </option>
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Integration")} name="serviceConnection">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<ServiceConnection[]> => {
                        const args: OutpostsServiceConnectionsAllListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const items = await new OutpostsApi(
                            DEFAULT_CONFIG,
                        ).outpostsServiceConnectionsAllList(args);
                        return items.results;
                    }}
                    .renderElement=${(item: ServiceConnection): string => {
                        return item.name;
                    }}
                    .value=${(item: ServiceConnection | undefined): string | undefined => {
                        return item?.pk;
                    }}
                    .groupBy=${(items: ServiceConnection[]) => {
                        return groupBy(items, (item) => item.verboseName);
                    }}
                    .selected=${(item: ServiceConnection, items: ServiceConnection[]): boolean => {
                        let selected = this.instance?.serviceConnection === item.pk;
                        if (items.length === 1 && !this.instance) {
                            selected = true;
                        }
                        return selected;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Selecting an integration enables the management of the outpost by authentik.",
                    )}
                </p>
                <p class="pf-c-form__helper-text">
                    See
                    <a target="_blank" href="${docLink("/docs/outposts?utm_source=authentik")}"
                        >documentation</a
                    >.
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Applications")}
                ?required=${!this.embedded}
                name="providers"
            >
                <select class="pf-c-form-control" multiple>
                    ${this.providers?.results.map((provider) => {
                        const selected = Array.from(this.instance?.providers || []).some((sp) => {
                            return sp == provider.pk;
                        });
                        let appName = provider.assignedApplicationName;
                        if (provider.assignedBackchannelApplicationName) {
                            appName = provider.assignedBackchannelApplicationName;
                        }
                        return html`<option value=${ifDefined(provider.pk)} ?selected=${selected}>
                            ${appName} (${provider.name})
                        </option>`;
                    })}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("You can only select providers that match the type of the outpost.")}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg("Hold control/command to select multiple items.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Configuration")} name="config">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(
                        this.instance ? this.instance.config : this.defaultConfig?.config,
                    )}"
                ></ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg("See more here:")}&nbsp;
                    <a
                        target="_blank"
                        href="${docLink("/docs/outposts?utm_source=authentik#configuration")}"
                        >${msg("Documentation")}</a
                    >
                </p>
            </ak-form-element-horizontal>`;
    }
}
