import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ascii_letters, digits, first, punctuation, randomString } from "@goauthentik/common/utils";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement } from "lit/decorators.js";

import {
    Enctype,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    KerberosRealm,
    ProvidersApi,
} from "@goauthentik/api";

@customElement("ak-kerberos-realm-form")
export class KerberosRealmFormPage extends ModelForm<KerberosRealm, number> {
    loadInstance(pk: number): Promise<KerberosRealm> {
        return new ProvidersApi(DEFAULT_CONFIG).providersKerberosRealmsRetrieve({
            id: pk,
        });
    }

    async load(): Promise<void> {
        this.enctypes = await new ProvidersApi(DEFAULT_CONFIG).providersKerberosEnctypesList();
    }

    enctypes?: Array<Enctype>;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated realm.");
        } else {
            return msg("Successfully created realm.");
        }
    }

    async send(data: KerberosRealm): Promise<KerberosRealm> {
        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersKerberosRealmsUpdate({
                id: this.instance.pk || 0,
                kerberosRealmRequest: data,
            });
        } else {
            return new ProvidersApi(DEFAULT_CONFIG).providersKerberosRealmsCreate({
                kerberosRealmRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Used for display and for your convenience")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Realm name")}
                ?required=${true}
                name="realmName"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.realmName)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">${msg("Name of the realm")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authentication flow")}
                ?required=${true}
                name="authenticationFlow"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Authentication,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
                        return flows.results;
                    }}
                    .renderElement=${(flow: Flow): string => {
                        return RenderFlowOption(flow);
                    }}
                    .renderDescription=${(flow: Flow): TemplateResult => {
                        return html`${flow.slug}`;
                    }}
                    .value=${(flow: Flow | undefined): string | undefined => {
                        return flow?.pk;
                    }}
                    .selected=${(flow: Flow): boolean => {
                        let selected = flow.pk === rootInterface()?.tenant?.flowAuthentication;
                        if (this.instance?.authenticationFlow === flow.pk) {
                            selected = true;
                        }
                        return selected;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">${msg("Flow used for users to authenticate.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Secret")} ?required=${true} name="secret">
                <input
                    type="text"
                    value="${first(
                        this.instance?.secret,
                        randomString(128, ascii_letters + digits + punctuation),
                    )}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Secret key used by the KDC to encrypt responses and TGT.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Maximum ticket lifetime")}
                        name="maximumTicketLifetime"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.maximumTicketLifetime, "days=1")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Maximum ticket lifetime (Format: hours=1;minutes=2;seconds=3).")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Maximum ticket renew lifetime")}
                        name="maximumTicketRenewLifetime"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.maximumTicketRenewLifetime, "weeks=1")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Maximum ticket lifetime (Format: hours=1;minutes=2;seconds=3).")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>

            <ak-form-group .expanded=${false}>
                <span slot="header"> ${msg("Advanced protocol settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Maximum skew")} name="maximumSkew">
                        <input
                            type="text"
                            value="${first(this.instance?.maximumSkew, "minutes=5")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Maximum allowed clock drift between the client and the server (Format: hours=1;minutes=2;seconds=3).",
                            )}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Allowed encryption types")}
                        ?required=${false}
                        name="allowedEnctypes"
                    >
                        <select class="pf-c-form-control" multiple>
                            ${this.enctypes?.map((enctype) => {
                                let selected = Array.from(
                                    this.instance?.allowedEnctypes || [],
                                ).some((e) => {
                                    return e == enctype.id;
                                });
                                // Creating a new instance, auto-select everything
                                if (!this.instance) {
                                    selected = true;
                                }
                                return html`<option
                                    value=${ifDefined(enctype.id)}
                                    ?selected=${selected}
                                >
                                    ${enctype.name}
                                </option>`;
                            })}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Which encryption types are allowed.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="allowPostdateable">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.allowPostdateable, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Allow postdateable")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Should the user be able to request a ticket with a start time in the future.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="allowRenewable">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.allowRenewable, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Allow renewable")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Should the service getting the ticket be able to use it on behalf of the user.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="allowProxiable">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.allowProxiable, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Allow proxiable")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Should the service getting the ticket be able to use it on behalf of the user.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="allowForwardable">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.allowForwardable, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Allow forwardable")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Should the service getting the ticket be able to request a TGT on behalf of the user.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="requiresPreauth">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.requiresPreauth, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${msg("Requires preauthentication")}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg("Should tickets only be issued to preauthenticated clients.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="setOkAsDelegate">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.setOkAsDelegate, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Set ok as delegeate")}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Should the tickets issued for this realm have the ok-as-delegate flag set.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
