import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import { Application, CoreApi, PolicyTestResult } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-application-check-access-form")
export class ApplicationCheckAccessForm extends Form<{ forUser: number }> {
    @property({ attribute: false })
    application!: Application;

    @property({ attribute: false })
    result?: PolicyTestResult;

    @property({ attribute: false })
    request?: number;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: { forUser: number }): Promise<PolicyTestResult> => {
        this.request = data.forUser;
        return new CoreApi(DEFAULT_CONFIG)
            .coreApplicationsCheckAccessRetrieve({
                slug: this.application?.slug,
                forUser: data.forUser,
            })
            .then((result) => (this.result = result));
    };

    resetForm(): void {
        super.resetForm();
        this.result = undefined;
    }

    renderResult(): TemplateResult {
        return html` <ak-form-element-horizontal label=${t`Passing`}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text"
                            >${this.result?.passing ? t`Yes` : t`No`}</span
                        >
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
            </ak-form-element-horizontal>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`User`} ?required=${true} name="forUser">
                <select class="pf-c-form-control">
                    ${until(
                        new CoreApi(DEFAULT_CONFIG)
                            .coreUsersList({
                                ordering: "username",
                            })
                            .then((users) => {
                                return users.results.map((user) => {
                                    return html`<option
                                        ?selected=${user.pk.toString() === this.request?.toString()}
                                        value=${user.pk}
                                    >
                                        ${user.username}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : html``}
        </form>`;
    }
}
