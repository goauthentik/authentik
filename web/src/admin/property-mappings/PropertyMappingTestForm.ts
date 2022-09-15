import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { UserOption } from "@goauthentik/elements/user/utils";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import {
    CoreApi,
    PolicyTestRequest,
    PropertyMapping,
    PropertyMappingTestResult,
    PropertymappingsApi,
} from "@goauthentik/api";

@customElement("ak-property-mapping-test-form")
export class PropertyMappingTestForm extends Form<PolicyTestRequest> {
    @property({ attribute: false })
    mapping?: PropertyMapping;

    @property({ attribute: false })
    result?: PropertyMappingTestResult;

    @property({ attribute: false })
    request?: PolicyTestRequest;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: PolicyTestRequest): Promise<PropertyMappingTestResult> => {
        this.request = data;
        return new PropertymappingsApi(DEFAULT_CONFIG)
            .propertymappingsAllTestCreate({
                pmUuid: this.mapping?.pk || "",
                policyTestRequest: data,
                formatResult: true,
            })
            .then((result) => (this.result = result));
    };

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
                <select class="pf-c-form-control">
                    ${until(
                        new CoreApi(DEFAULT_CONFIG)
                            .coreUsersList({
                                ordering: "username",
                            })
                            .then((users) => {
                                return users.results.map((user) => {
                                    return html`<option
                                        ?selected=${this.request?.user.toString() ===
                                        user.pk.toString()}
                                        value=${user.pk}
                                    >
                                        ${UserOption(user)}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
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
