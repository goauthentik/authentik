import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { Form } from "#elements/forms/Form";
import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { CoreApi, Stage, StagesApi, User, UserRecoveryEmailRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

const emailStageSource: SearchSelectSource<Stage> = {
    fetchObjects: (query) =>
        aki(StagesApi)
            .stagesEmailList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (stage) => stage.pk,
    labelOf: (stage) => stage.name,
    groupBy: (stages) => groupBy(stages, (stage) => stage.verboseNamePlural),
};

@customElement("ak-user-reset-email-form")
export class UserResetEmailForm extends Form<UserRecoveryEmailRequest> {
    public override submitLabel = msg("Send link");
    public override headline = msg("Send recovery link to user");

    @property({ attribute: false })
    public user!: User;

    public override getSuccessMessage(): string {
        return msg("Successfully queued email.");
    }

    async send(data: UserRecoveryEmailRequest): Promise<void> {
        return aki(CoreApi).coreUsersRecoveryEmailCreate({
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
                ${AKSearchSelect({
                    name: "emailStage",
                    source: emailStageSource,
                    placeholder: msg("Select email stage..."),
                    blankable: false,
                })}
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
