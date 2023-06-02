import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreUsersListRequest,
    PolicyTestRequest,
    PropertyMapping,
    PropertyMappingTestResult,
    PropertymappingsApi,
    User,
} from "@goauthentik/api";

@customElement("ak-property-mapping-test-form")
export class PolicyTestForm extends Form<PolicyTestRequest> {
    @property({ attribute: false })
    mapping?: PropertyMapping;

    @property({ attribute: false })
    result?: PropertyMappingTestResult;

    @property({ attribute: false })
    request?: PolicyTestRequest;

    getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    async send(data: PolicyTestRequest): Promise<PropertyMappingTestResult> {
        this.request = data;
        const result = await new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTestCreate({
            pmUuid: this.mapping?.pk || "",
            policyTestRequest: data,
            formatResult: true,
        });
        return (this.result = result);
    }

    renderResult(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Result")}>
            ${this.result?.successful
                ? html`<ak-codemirror
                      mode="javascript"
                      ?readOnly=${true}
                      value="${ifDefined(this.result?.result)}"
                  >
                  </ak-codemirror>`
                : html` <div class="pf-c-form__group-label">
                      <div class="c-form__horizontal-group">
                          <span class="pf-c-form__label-text">${this.result?.result}</span>
                      </div>
                  </div>`}
        </ak-form-element-horizontal>`;
    }

    renderExampleButtons(): TemplateResult {
        const header = html`<p>${msg("Example context data")}</p>`;
        switch (this.mapping?.metaModelName) {
            case "authentik_sources_ldap.ldappropertymapping":
                return html`${header}${this.renderExampleLDAP()}`;
            default:
                return html``;
        }
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
                                name: "test-user",
                                objectSid: "S-1-5-21-2611707862-2219215769-354220275-1137",
                                objectClass: "person",
                                displayName: "authentik test user",
                                sAMAccountName: "sAMAccountName",
                                distinguishedName: "cn=user,ou=users,dc=goauthentik,dc=io",
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
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("User")} ?required=${true} name="user">
                <ak-search-select
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
                        return this.request?.user.toString() === user.pk.toString();
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Context")} name="context">
                <ak-codemirror
                    mode="yaml"
                    value=${YAML.stringify(first(this.request?.context, {}))}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${this.renderExampleButtons()}</p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
