import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import "@goauthentik/web/elements/CodeMirror";
import { PFColor } from "@goauthentik/web/elements/Label";
import { Form } from "@goauthentik/web/elements/forms/Form";
import "@goauthentik/web/elements/forms/HorizontalFormElement";
import { UserOption } from "@goauthentik/web/elements/user/utils";
import { first } from "@goauthentik/web/utils";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import {
    CoreApi,
    PoliciesApi,
    Policy,
    PolicyTestRequest,
    PolicyTestResult,
} from "@goauthentik/api";

@customElement("ak-policy-test-form")
export class PolicyTestForm extends Form<PolicyTestRequest> {
    @property({ attribute: false })
    policy?: Policy;

    @property({ attribute: false })
    result?: PolicyTestResult;

    @property({ attribute: false })
    request?: PolicyTestRequest;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: PolicyTestRequest): Promise<PolicyTestResult> => {
        this.request = data;
        return new PoliciesApi(DEFAULT_CONFIG)
            .policiesAllTestCreate({
                policyUuid: this.policy?.pk || "",
                policyTestRequest: data,
            })
            .then((result) => (this.result = result));
    };

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${t`Passing`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-label color=${this.result?.passing ? PFColor.Green : PFColor.Red}>
                                ${this.result?.passing ? t`Yes` : t`No`}
                            </ak-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Messages`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <ul>
                            ${(this.result?.messages || []).length > 0
                                ? this.result?.messages?.map((m) => {
                                      return html`<li>
                                          <span class="pf-c-form__label-text">${m}</span>
                                      </li>`;
                                  })
                                : html`<li>
                                      <span class="pf-c-form__label-text">-</span>
                                  </li>`}
                        </ul>
                    </div>
                </div>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${t`Log messages`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            ${(this.result?.logMessages || []).length > 0
                                ? this.result?.logMessages?.map((m) => {
                                      return html`<div class="pf-c-description-list__group">
                                          <dt class="pf-c-description-list__term">
                                              <span class="pf-c-description-list__text"
                                                  >${m.log_level}</span
                                              >
                                          </dt>
                                          <dd class="pf-c-description-list__description">
                                              <div class="pf-c-description-list__text">
                                                  ${m.event}
                                              </div>
                                          </dd>
                                      </div>`;
                                  })
                                : html`<div class="pf-c-description-list__group">
                                      <dt class="pf-c-description-list__term">
                                          <span class="pf-c-description-list__text"
                                              >${t`No log messages.`}</span
                                          >
                                      </dt>
                                  </div>`}
                        </dl>
                    </div>
                </div>
            </ak-form-element-horizontal>
        `;
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
                <p class="pf-c-form__helper-text">
                    ${t`Set custom attributes using YAML or JSON.`}
                </p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
