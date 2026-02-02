import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { Form } from "#elements/forms/Form";

import {
    CoreApi,
    Stage,
    StagesAllListRequest,
    StagesApi,
    User,
    UserRecoveryEmailRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-reset-email-form")
export class UserResetEmailForm extends Form<UserRecoveryEmailRequest> {
    @property({ attribute: false })
    user!: User;

    getSuccessMessage(): string {
        return msg("Successfully sent email.");
    }

    async send(data: UserRecoveryEmailRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryEmailCreate({
            id: this.user.pk,
            userRecoveryEmailRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal
                label=${msg("Email stage")}
                required
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
            </ak-form-element-horizontal>
            <ak-text-input
                name="tokenDuration"
                label=${msg("Token duration")}
                value="days=1"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                    ${msg("If a recovery token already exists, its duration is updated.")}
                </p>`}
            >
            </ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-reset-email-form": UserResetEmailForm;
    }
}
