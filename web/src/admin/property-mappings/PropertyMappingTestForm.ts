import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import * as YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    CoreUsersListRequest,
    Group,
    PropertyMapping,
    PropertyMappingTestRequest,
    PropertyMappingTestResult,
    PropertymappingsApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    User,
} from "@goauthentik/api";

@customElement("ak-property-mapping-test-form")
export class PolicyTestForm extends Form<PropertyMappingTestRequest> {
    @property({ attribute: false })
    mapping?: PropertyMapping;

    @property({ attribute: false })
    result?: PropertyMappingTestResult;

    @property({ attribute: false })
    request?: PropertyMappingTestRequest;

    getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    async send(data: PropertyMappingTestRequest): Promise<PropertyMappingTestResult> {
        this.request = data;
        const result = await new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTestCreate({
            pmUuid: this.mapping?.pk || "",
            propertyMappingTestRequest: data,
            formatResult: true,
        });
        return (this.result = result);
    }

    renderResult(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Result")}>
            ${this.result?.successful
                ? html`<ak-codemirror
                      mode=${CodeMirrorMode.JavaScript}
                      ?readOnly=${true}
                      value="${ifDefined(this.result?.result)}"
                  >
                  </ak-codemirror>`
                : html` <div class="pf-c-form__group-label">
                      <div class="c-form__horizontal-group">
                          <span class="pf-c-form__label-text">
                              <pre>${this.result?.result}</pre>
                          </span>
                      </div>
                  </div>`}
        </ak-form-element-horizontal>`;
    }

    renderExampleButtons() {
        return this.mapping?.metaModelName ===
            RbacPermissionsAssignedByUsersListModelEnum.AuthentikSourcesLdapLdapsourcepropertymapping
            ? html`<p>${msg("Example context data")}</p>
                  ${this.renderExampleLDAP()}`
            : nothing;
    }

    renderExampleLDAP(): TemplateResult {
        return html`
            <button
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

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} name="user">
                <ak-search-select
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
                    .renderDescription=${(user: User): TemplateResult => {
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
            <ak-form-element-horizontal label=${msg("Context")} name="context">
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value=${YAML.stringify(first(this.request?.context, {}))}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${this.renderExampleButtons()}</p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-test-form": PolicyTestForm;
    }
}
