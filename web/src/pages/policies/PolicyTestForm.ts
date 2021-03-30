import { CoreApi, PoliciesApi, Policy, PolicyTestResult } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import { PolicyTest } from "authentik-api/src";

@customElement("ak-policy-test-form")
export class PolicyTestForm extends Form<PolicyTest> {

    @property({attribute: false})
    policy?: Policy;

    @property({ attribute: false})
    result?: PolicyTestResult;

    getSuccessMessage(): string {
        return gettext("Successfully sent test-request.");
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
                label=${gettext("Passing")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">${this.result?.passing ? gettext("Yes") : gettext("No")}</span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Messages")}>
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
                label=${gettext("User")}
                ?required=${true}
                name="user">
                <select class="pf-c-form-control">
                    ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({
                        ordering: "username",
                    }).then(users => {
                        return users.results.map(user => {
                            return html`<option value=${ifDefined(user.pk)}>${user.username}</option>`;
                        });
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Context")}
                name="context">
                <ak-codemirror mode="yaml">
                </ak-codemirror>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult(): html``}
        </form>`;
    }

}
