import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { t } from "@lingui/macro";

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
        return t`Successfully sent test-request.`;
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
        return html`<ak-form-element-horizontal label=${t`Result`}>
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

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`User`} ?required=${true} name="user">
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
            <ak-form-element-horizontal label=${t`Context`} name="context">
                <ak-codemirror mode="yaml" value=${YAML.stringify(first(this.request?.context, {}))}
                    >>
                </ak-codemirror>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
