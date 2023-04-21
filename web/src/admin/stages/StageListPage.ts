import "@goauthentik/admin/stages/StageWizard";
import "@goauthentik/admin/stages/authenticator_duo/AuthenticatorDuoStageForm";
import "@goauthentik/admin/stages/authenticator_duo/DuoDeviceImportForm";
import "@goauthentik/admin/stages/authenticator_sms/AuthenticatorSMSStageForm";
import "@goauthentik/admin/stages/authenticator_static/AuthenticatorStaticStageForm";
import "@goauthentik/admin/stages/authenticator_totp/AuthenticatorTOTPStageForm";
import "@goauthentik/admin/stages/authenticator_validate/AuthenticatorValidateStageForm";
import "@goauthentik/admin/stages/authenticator_webauthn/AuthenticateWebAuthnStageForm";
import "@goauthentik/admin/stages/captcha/CaptchaStageForm";
import "@goauthentik/admin/stages/consent/ConsentStageForm";
import "@goauthentik/admin/stages/deny/DenyStageForm";
import "@goauthentik/admin/stages/dummy/DummyStageForm";
import "@goauthentik/admin/stages/email/EmailStageForm";
import "@goauthentik/admin/stages/identification/IdentificationStageForm";
import "@goauthentik/admin/stages/invitation/InvitationStageForm";
import "@goauthentik/admin/stages/password/PasswordStageForm";
import "@goauthentik/admin/stages/prompt/PromptStageForm";
import "@goauthentik/admin/stages/user_delete/UserDeleteStageForm";
import "@goauthentik/admin/stages/user_login/UserLoginStageForm";
import "@goauthentik/admin/stages/user_logout/UserLogoutStageForm";
import "@goauthentik/admin/stages/user_write/UserWriteStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

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

    async apiEndpoint(page: number): Promise<PaginatedResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
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

    renderStageActions(stage: Stage): TemplateResult {
        switch (stage.component) {
            case "ak-stage-authenticator-duo-form":
                return html`<ak-forms-modal>
                    <span slot="submit">${t`Import`}</span>
                    <span slot="header">${t`Import Duo device`}</span>
                    <ak-stage-authenticator-duo-device-import-form
                        slot="form"
                        .instancePk=${stage.pk}
                    >
                    </ak-stage-authenticator-duo-device-import-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-file-import"></i>
                    </button>
                </ak-forms-modal>`;
            default:
                return html``;
        }
    }

    row(item: Stage): TemplateResult[] {
        return [
            html`<div>${item.name}</div>
                <small>${item.verboseName}</small>`,
            html`<ul class="pf-c-list">
                ${item.flowSet?.map((flow) => {
                    return html`<li>
                        <a href="#/flow/flows/${flow.slug}">
                            <code>${flow.slug}</code>
                        </a>
                    </li>`;
                })}
            </ul>`,
            html`<ak-forms-modal>
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
                </ak-forms-modal>
                ${this.renderStageActions(item)}`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-stage-wizard></ak-stage-wizard> `;
    }
}
