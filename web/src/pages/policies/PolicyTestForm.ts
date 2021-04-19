import { CoreApi, PoliciesApi, Policy, PolicyTestResult } from "authentik-api";
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

@customElement("ak-policy-test-form")
export class PolicyTestForm extends Form<PolicyTest> {

    @property({attribute: false})
    policy?: Policy;

    @property({ attribute: false})
    result?: PolicyTestResult;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: PolicyTest): Promise<PolicyTestResult> => {
        return new PoliciesApi(DEFAULT_CONFIG).policiesAllTest({
            policyUuid: this.policy?.pk || "",
            data: data
        }).then(result => this.result = result);
    };

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${t`Passing`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">${this.result?.passing ? t`Yes` : t`No`}</span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Messages`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <ul>
                            ${(this.result?.messages || []).length > 0 ?
                            this.result?.messages?.map(m => {
                                return html`<li><span class="pf-c-form__label-text">${m}</span></li>`;
                            }) :
                            html`<li><span class="pf-c-form__label-text">-</span></li>`}
                        </ul>
                    </div>
                </div>
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
                <ak-codemirror mode="yaml" value=${YAML.stringify({})}>>
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${t`Set custom attributes using YAML or JSON.`}</p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult(): html``}
        </form>`;
    }

}
