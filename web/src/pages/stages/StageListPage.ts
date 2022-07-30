import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import "@goauthentik/web/elements/forms/DeleteBulkForm";
import "@goauthentik/web/elements/forms/ModalForm";
import "@goauthentik/web/elements/forms/ProxyForm";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TablePage } from "@goauthentik/web/elements/table/TablePage";
import "@goauthentik/web/pages/stages/StageWizard";
import "@goauthentik/web/pages/stages/authenticator_duo/AuthenticatorDuoStageForm";
import "@goauthentik/web/pages/stages/authenticator_sms/AuthenticatorSMSStageForm";
import "@goauthentik/web/pages/stages/authenticator_static/AuthenticatorStaticStageForm";
import "@goauthentik/web/pages/stages/authenticator_totp/AuthenticatorTOTPStageForm";
import "@goauthentik/web/pages/stages/authenticator_validate/AuthenticatorValidateStageForm";
import "@goauthentik/web/pages/stages/authenticator_webauthn/AuthenticateWebAuthnStageForm";
import "@goauthentik/web/pages/stages/captcha/CaptchaStageForm";
import "@goauthentik/web/pages/stages/consent/ConsentStageForm";
import "@goauthentik/web/pages/stages/deny/DenyStageForm";
import "@goauthentik/web/pages/stages/dummy/DummyStageForm";
import "@goauthentik/web/pages/stages/email/EmailStageForm";
import "@goauthentik/web/pages/stages/identification/IdentificationStageForm";
import "@goauthentik/web/pages/stages/invitation/InvitationStageForm";
import "@goauthentik/web/pages/stages/password/PasswordStageForm";
import "@goauthentik/web/pages/stages/prompt/PromptStageForm";
import "@goauthentik/web/pages/stages/user_delete/UserDeleteStageForm";
import "@goauthentik/web/pages/stages/user_login/UserLoginStageForm";
import "@goauthentik/web/pages/stages/user_logout/UserLogoutStageForm";
import "@goauthentik/web/pages/stages/user_write/UserWriteStageForm";
import { groupBy } from "@goauthentik/web/utils";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Stage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    pageTitle(): string {
        return t`Stages`;
    }
    pageDescription(): string | undefined {
        return t`Stages are single steps of a Flow that a user is guided through. A stage can only be executed from within a flow.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-plugged";
    }
    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<AKResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    groupBy(items: Stage[]): [string, Stage[]][] {
        return groupBy(items, (stage) => stage.verboseNamePlural);
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Flows`),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Stage(s)`}
            .objects=${this.selectedElements}
            .usedBy=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllUsedByList({
                    stageUuid: item.pk,
                });
            }}
            .delete=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllDestroy({
                    stageUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: Stage): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
                <small>${item.verboseName}</small>
            </div>`,
            html`<ul class="pf-c-list">
                ${item.flowSet?.map((flow) => {
                    return html`<li>
                        <a href="#/flow/flows/${flow.slug}">
                            <code>${flow.slug}</code>
                        </a>
                    </li>`;
                })}
            </ul>`,
            html` <ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update ${item.verboseName}`} </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        instancePk: item.pk,
                    }}
                    type=${ifDefined(item.component)}
                >
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-stage-wizard></ak-stage-wizard> `;
    }
}
