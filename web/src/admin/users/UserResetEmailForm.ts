import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    CoreApi,
    CoreUsersRecoveryEmailRetrieveRequest,
    Stage,
    StagesAllListRequest,
    StagesApi,
    User,
} from "@goauthentik/api";

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
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Stage[]> => {
                        const args: StagesAllListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const stages = await new StagesApi(DEFAULT_CONFIG).stagesEmailList(args);
                        return stages.results;
                    }}
                    .groupBy=${(items: Stage[]) => {
                        return groupBy(items, (stage) => stage.verboseNamePlural);
                    }}
                    .renderElement=${(stage: Stage): string => {
                        return stage.name;
                    }}
                    .value=${(stage: Stage | undefined): string | undefined => {
                        return stage?.pk;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
        </form>`;
    }
}
