import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import {
    CoreApi,
    CoreGroupsListRequest,
    CoreUsersListRequest,
    Group,
    ModelEnum,
    PropertyMapping,
    PropertymappingsApi,
    PropertyMappingTestRequest,
    PropertyMappingTestResult,
    User,
} from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-property-mapping-test-form")
export class PropertyMappingTestForm extends Form<PropertyMappingTestRequest> {
    public static verboseName = msg("Property Mapping");
    public static verboseNamePlural = msg("Property Mappings");
    public static createLabel = msg("Test");

    public override cancelable = true;
    public override size = PFSize.XLarge;

    #api = new PropertymappingsApi(DEFAULT_CONFIG);

    protected override formatSubmitLabel(submitLabel?: string | null): string {
        return submitLabel || msg("Run Test");
    }

    @property({ attribute: false })
    public mapping: PropertyMapping | null = null;

    @property({ attribute: false })
    public result: PropertyMappingTestResult | null = null;

    @property({ attribute: false })
    public request: PropertyMappingTestRequest | null = null;

    public override getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    protected override async send(
        data: PropertyMappingTestRequest,
    ): Promise<PropertyMappingTestResult> {
        this.request = data;

        this.result = await this.#api.propertymappingsAllTestCreate({
            pmUuid: this.mapping?.pk || "",
            propertyMappingTestRequest: data,
            formatResult: true,
        });

        return this.result;
    }

    public get verboseName(): string | null {
        return this.mapping?.verboseName || null;
    }

    public get verboseNamePlural(): string | null {
        return this.mapping?.verboseNamePlural || null;
    }

    protected renderResult(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal>
            ${this.result?.successful
                ? html`${AKLabel(
                          {
                              slot: "label",
                              className: "pf-c-form__group-label",
                              htmlFor: "result",
                          },
                          msg("Result"),
                      )}

                      <ak-codemirror
                          id="result"
                          mode="javascript"
                          readonly
                          value="${ifDefined(this.result?.result)}"
                      >
                      </ak-codemirror>`
                : html`<div class="pf-c-form__group-label">
                      <div class="c-form__horizontal-group">
                          <span class="pf-c-form__label-text">
                              <pre>${this.result?.result}</pre>
                          </span>
                      </div>
                  </div>`}
        </ak-form-element-horizontal>`;
    }

    protected renderExampleButtons(): SlottedTemplateResult {
        if (
            this.mapping?.metaModelName !== ModelEnum.AuthentikSourcesLdapLdapsourcepropertymapping
        ) {
            return null;
        }

        return html`<div class="pf-c-form__group">
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                },
                msg("Example Context Data"),
            )}
            <p class="pf-c-form__helper-text">${this.renderExampleLDAP()}</p>
        </div>`;
    }

    protected renderExampleLDAP(): SlottedTemplateResult {
        return html`
            <button
                type="button"
                class="pf-c-button pf-m-secondary"
                role="button"
                @click=${() => {
                    this.request = {
                        user: this.request?.user || 0,
                        context: {
                            ldap: {
                                displayName: "authentik test user",
                                distinguishedName: "cn=user,ou=users,dc=goauthentik,dc=io",
                                givenName: "test",
                                name: "test-user",
                                objectClass: "person",
                                objectSid: "S-1-5-21-2611707862-2219215769-354220275-1137",
                                sAMAccountName: "sAMAccountName",
                                sn: "user",
                            },
                        },
                    };
                }}
            >
                ${msg("Active Directory User")}
            </button>
            <button
                type="button"
                class="pf-c-button pf-m-secondary"
                role="button"
                @click=${() => {
                    this.request = {
                        user: this.request?.user || 0,
                        context: {
                            ldap: {
                                name: "test-group",
                                objectSid: "S-1-5-21-2611707862-2219215769-354220275-1137",
                                objectClass: "group",
                                distinguishedName: "cn=group,ou=groups,dc=goauthentik,dc=io",
                            },
                        },
                    };
                }}
            >
                ${msg("Active Directory Group")}
            </button>
        `;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} name="user">
                <ak-search-select
                    placeholder=${msg("Select a user...")}
                    blankable
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): SlottedTemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
                    }}
                    .selected=${(user: User): boolean => {
                        return this.request?.user?.toString() === user.pk.toString();
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Group")} name="group">
                <ak-search-select
                    placeholder=${msg("Select a group...")}
                    blankable
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                        return groups.results;
                    }}
                    .renderElement=${(group: Group): string => {
                        return group.name;
                    }}
                    .value=${(group: Group | undefined): string | undefined => {
                        return group?.pk;
                    }}
                    .selected=${(group: Group): boolean => {
                        return this.request?.group?.toString() === group.pk.toString();
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            ${this.renderExampleButtons()}

            <ak-form-element-horizontal name="context">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "context",
                    },
                    msg("Context"),
                )}
                <ak-codemirror
                    id="context"
                    mode="yaml"
                    value=${YAML.stringify(this.request?.context ?? {})}
                >
                </ak-codemirror>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : null}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-test-form": PropertyMappingTestForm;
    }
}
