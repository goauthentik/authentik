import { DataProvider, DualSelectPair } from "@goauthentik/app/elements/ak-dual-select/types";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/ak-dual-select/ak-dual-select-provider";
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
    Pagination,
    ProvidersApi,
    ServiceConnection,
} from "@goauthentik/api";

interface ProviderBase {
    pk: number;
    name: string;
    assignedBackchannelApplicationName?: string;
    assignedApplicationName?: string;
}

interface ProviderData {
    pagination: Pagination;
    results: ProviderBase[];
}

const api = () => new ProvidersApi(DEFAULT_CONFIG);
const providerListArgs = (page: number) => ({
    ordering: "name",
    applicationIsnull: false,
    pageSize: 20,
    search: "",
    page,
});

const dualSelectPairMaker = (item: ProviderBase): DualSelectPair => [
    `${item.pk}`,
    `${
        item.assignedBackchannelApplicationName
            ? item.assignedBackchannelApplicationName
            : item.assignedApplicationName
    } (${item.name})`,
];

const provisionMaker = (results: ProviderData) => ({
    pagination: results.pagination,
    options: results.results.map(dualSelectPairMaker),
});

const proxyListFetch = async (page: number) =>
    provisionMaker(await api().providersProxyList(providerListArgs(page)));

const ldapListFetch = async (page: number) =>
    provisionMaker(await api().providersLdapList(providerListArgs(page)));

const radiusListFetch = async (page: number) =>
    provisionMaker(await api().providersRadiusList(providerListArgs(page)));

const racListProvider = async (page: number) =>
    provisionMaker(await api().providersRacList(providerListArgs(page)));

function providerProvider(type: OutpostTypeEnum): DataProvider {
    switch (type) {
        case OutpostTypeEnum.Proxy:
            return proxyListFetch;
        case OutpostTypeEnum.Ldap:
            return ldapListFetch;
        case OutpostTypeEnum.Radius:
            return radiusListFetch;
        case OutpostTypeEnum.Rac:
            return racListProvider;
        default:
            throw new Error(`Unrecognized OutputType: ${type}`);
    }
}

@customElement("ak-outpost-form")
export class OutpostForm extends ModelForm<Outpost, string> {
    @property()
    type: OutpostTypeEnum = OutpostTypeEnum.Proxy;

    @property({ type: Boolean })
    embedded = false;

    @state()
    providers?: DataProvider;
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
        this.providers = providerProvider(this.type);
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated outpost.")
            : msg("Successfully created outpost.");
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
                    <option
                        value=${OutpostTypeEnum.Rac}
                        ?selected=${this.instance?.type === OutpostTypeEnum.Rac}
                    >
                        ${msg("RAC")}
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
                <ak-dual-select-provider
                    .provider=${this.providers}
                    .selected=${(this.instance?.providersObj ?? []).map(dualSelectPairMaker)}
                    available-label="${msg("Available Applications")}"
                    selected-label="${msg("Selected Applications")}"
                ></ak-dual-select-provider>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Configuration")} name="config">
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
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
