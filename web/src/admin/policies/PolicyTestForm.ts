import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { PFColor } from "@goauthentik/elements/Label";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import {
    CoreApi,
    CoreUsersListRequest,
    PoliciesApi,
    Policy,
    PolicyTestRequest,
    PolicyTestResult,
    User,
} from "@goauthentik/api";

@customElement("ak-policy-test-form")
export class PolicyTestForm extends Form<PolicyTestRequest> {
    @property({ attribute: false })
    policy?: Policy;

    @state()
    result?: PolicyTestResult;

    @property({ attribute: false })
    request?: PolicyTestRequest;

    getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    async send(data: PolicyTestRequest): Promise<PolicyTestResult> {
        this.request = data;
        const result = await new PoliciesApi(DEFAULT_CONFIG).policiesAllTestCreate({
            policyUuid: this.policy?.pk || "",
            policyTestRequest: data,
        });
        return (this.result = result);
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFDescriptionList);
    }

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Passing")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-label color=${this.result?.passing ? PFColor.Green : PFColor.Red}>
                                ${this.result?.passing ? msg("Yes") : msg("No")}
                            </ak-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Messages")}>
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

            <ak-form-element-horizontal label=${msg("Log messages")}>
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
                                              >${msg("No log messages.")}</span
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
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
