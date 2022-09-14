import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import { CoreApi, CoreUsersRecoveryEmailRetrieveRequest, StagesApi, User } from "@goauthentik/api";

@customElement("ak-user-reset-email-form")
export class UserResetEmailForm extends Form<CoreUsersRecoveryEmailRetrieveRequest> {
    @property({ attribute: false })
    user!: User;

    getSuccessMessage(): string {
        return t`Successfully sent email.`;
    }

    send = (data: CoreUsersRecoveryEmailRetrieveRequest): Promise<void> => {
        data.id = this.user.pk;
        return new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryEmailRetrieve(data);
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Email stage`} ?required=${true} name="emailStage">
                <select class="pf-c-form-control">
                    ${until(
                        new StagesApi(DEFAULT_CONFIG)
                            .stagesEmailList({
                                ordering: "name",
                            })
                            .then((stages) => {
                                return stages.results.map((stage) => {
                                    return html`<option value=${stage.pk}>${stage.name}</option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
            </ak-form-element-horizontal>
        </form>`;
    }
}
