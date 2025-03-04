import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-text-input";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect";
import { writeToClipboard } from "@goauthentik/elements/utils/writeToClipboard";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    CoreApi,
    CoreUsersRecoveryLinkCreateRequest,
    Link,
    Stage,
    StagesAllListRequest,
    StagesApi,
    User,
} from "@goauthentik/api";

@customElement("ak-user-recovery-link-form")
export class UserRecoveryLinkForm extends Form<CoreUsersRecoveryLinkCreateRequest> {
    @property({ attribute: false })
    user!: User;

    @property({ type: Boolean })
    withEmailStage = false;

    async send(data: CoreUsersRecoveryLinkCreateRequest): Promise<Link> {
        data.id = this.user.pk;
        const response = await new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryLinkCreate(data);

        if (this.withEmailStage) {
            this.successMessage = msg("Successfully sent email.");
        } else {
            const wroteToClipboard = await writeToClipboard(response.link);
            if (wroteToClipboard) {
                this.successMessage = msg(
                    `A copy of this recovery link has been placed in your clipboard: ${response.link}`,
                );
            } else {
                this.successMessage = msg(
                    `authentik does not have access to your clipboard, please copy the recovery link manually: ${response.link}`,
                );
            }
        }

        return response;
    }

    renderEmailStageInput(): TemplateResult {
        if (!this.withEmailStage) return html``;
        return html`
            <ak-form-element-horizontal name="emailStage" label=${msg("Email stage")} required>
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
        `;
    }

    renderForm(): TemplateResult {
        return html`
            ${this.renderEmailStageInput()}
            <ak-text-input
                name="tokenDuration"
                label=${msg("Token duration")}
                required
                value="days=1"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                    ${msg("Duration for generated token")}
                </p>`}
            >
            </ak-text-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-recovery-link-form": UserRecoveryLinkForm;
    }
}
