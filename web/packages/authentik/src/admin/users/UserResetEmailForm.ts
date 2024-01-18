import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { groupBy } from "@goauthentik/common/utils.js";
import { Form } from "@goauthentik/elements/forms/Form.js";
import "@goauthentik/elements/forms/HorizontalFormElement.js";
import "@goauthentik/elements/forms/SearchSelect/ak-search-select.js";

import { msg } from "@lit/localize";
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
        return msg("Successfully sent email.");
    }

    async send(data: CoreUsersRecoveryEmailRetrieveRequest): Promise<void> {
        data.id = this.user.pk;
        return new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryEmailRetrieve(data);
    }

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal
            label=${msg("Email stage")}
            ?required=${true}
            name="emailStage"
        >
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
        </ak-form-element-horizontal>`;
    }
}
