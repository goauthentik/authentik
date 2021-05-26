import { Application, CoreApi, CheckAccessRequestRequest, PolicyTestResult } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { until } from "lit-html/directives/until";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-application-check-access-form")
export class ApplicationCheckAccessForm extends Form<CheckAccessRequestRequest> {

    @property({attribute: false})
    application!: Application;

    @property({ attribute: false})
    result?: PolicyTestResult;

    @property({ attribute: false})
    request?: CheckAccessRequestRequest;

    getSuccessMessage(): string {
        return t`Successfully sent test-request.`;
    }

    send = (data: CheckAccessRequestRequest): Promise<PolicyTestResult> => {
        this.request = data;
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsCheckAccessCreate({
            slug: this.application?.slug,
            checkAccessRequestRequest: data,
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
                name="forUser">
                <select class="pf-c-form-control">
                    ${until(new CoreApi(DEFAULT_CONFIG).coreUsersList({
                        ordering: "username",
                    }).then(users => {
                        return users.results.map(user => {
                            return html`<option ?selected=${user.pk.toString() === this.request?.forUser?.toString()} value=${user.pk}>${user.username}</option>`;
                        });
                    }), html`<option>${t`Loading...`}</option>`)}
                </select>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult(): html``}
        </form>`;
    }

}
