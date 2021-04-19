import { CoreApi, PropertyMapping, PropertymappingsApi, PropertyMappingTestResult } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import { PolicyTest } from "authentik-api/src";
import YAML from "yaml";

@customElement("ak-property-mapping-test-form")
export class PolicyTestForm extends Form<PolicyTest> {

    @property({attribute: false})
    mapping?: PropertyMapping;

    @property({ attribute: false})
    result?: PropertyMappingTestResult;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: PolicyTest): Promise<PropertyMappingTestResult> => {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTest({
            pmUuid: this.mapping?.pk || "",
            data: data,
            formatResult: true,
        }).then(result => this.result = result);
    };

    renderResult(): TemplateResult {
        return html`<ak-form-element-horizontal
                label=${t`Result`}>
            ${this.result?.successful ?
                html`<ak-codemirror mode="javascript" ?readOnly=${true} value="${ifDefined(this.result?.result)}">
                </ak-codemirror>`:
                html`
                    <div class="pf-c-form__group-label">
                        <div class="c-form__horizontal-group">
                            <span class="pf-c-form__label-text">${this.result?.result}</span>
                        </div>
                    </div>`}
        </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`User`}
                ?required=${true}
                name="user">
                <select class="pf-c-form-control">
                    ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({
                        ordering: "username",
                    }).then(users => {
                        return users.results.map(user => {
                            return html`<option value=${ifDefined(user.pk)}>${user.username}</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Context`}
                name="context">
                <ak-codemirror mode="yaml" value=${YAML.stringify({})}>
                </ak-codemirror>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult(): html``}
        </form>`;
    }

}
