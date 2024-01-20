import "@goauthentik/admin/stages/StageWizard.js";
import "@goauthentik/admin/stages/authenticator_duo/AuthenticatorDuoStageForm.js";
import "@goauthentik/admin/stages/authenticator_duo/DuoDeviceImportForm.js";
import "@goauthentik/admin/stages/authenticator_sms/AuthenticatorSMSStageForm.js";
import "@goauthentik/admin/stages/authenticator_static/AuthenticatorStaticStageForm.js";
import "@goauthentik/admin/stages/authenticator_totp/AuthenticatorTOTPStageForm.js";
import "@goauthentik/admin/stages/authenticator_validate/AuthenticatorValidateStageForm.js";
import "@goauthentik/admin/stages/authenticator_webauthn/AuthenticateWebAuthnStageForm.js";
import "@goauthentik/admin/stages/captcha/CaptchaStageForm.js";
import "@goauthentik/admin/stages/consent/ConsentStageForm.js";
import "@goauthentik/admin/stages/deny/DenyStageForm.js";
import "@goauthentik/admin/stages/dummy/DummyStageForm.js";
import "@goauthentik/admin/stages/email/EmailStageForm.js";
import "@goauthentik/admin/stages/identification/IdentificationStageForm.js";
import "@goauthentik/admin/stages/invitation/InvitationStageForm.js";
import "@goauthentik/admin/stages/password/PasswordStageForm.js";
import "@goauthentik/admin/stages/prompt/PromptStageForm.js";
import "@goauthentik/admin/stages/user_delete/UserDeleteStageForm.js";
import "@goauthentik/admin/stages/user_login/UserLoginStageForm.js";
import "@goauthentik/admin/stages/user_logout/UserLogoutStageForm.js";
import "@goauthentik/admin/stages/user_write/UserWriteStageForm.js";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { uiConfig } from "@goauthentik/common/ui/config.js";
import "@goauthentik/elements/forms/DeleteBulkForm.js";
import "@goauthentik/elements/forms/ModalForm.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import "@goauthentik/elements/rbac/ObjectPermissionModal.js";
import { PaginatedResponse } from "@goauthentik/elements/table/Table.js";
import { TableColumn } from "@goauthentik/elements/table/Table.js";
import { TablePage } from "@goauthentik/elements/table/TablePage.js";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Stage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    pageTitle(): string {
        return msg("Stages");
    }
    pageDescription(): string | undefined {
        return msg(
            "Stages are single steps of a Flow that a user is guided through. A stage can only be executed from within a flow.",
        );
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
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Flows")),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Stage(s)")}
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
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderStageActions(stage: Stage): TemplateResult {
        switch (stage.component) {
            case "ak-stage-authenticator-duo-form":
                return html`<ak-forms-modal>
                    <span slot="submit">${msg("Import")}</span>
                    <span slot="header">${msg("Import Duo device")}</span>
                    <ak-stage-authenticator-duo-device-import-form
                        slot="form"
                        .instancePk=${stage.pk}
                    >
                    </ak-stage-authenticator-duo-device-import-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Import devices")}>
                            <i class="fas fa-file-import" aria-hidden="true"></i>
                        </pf-tooltip>
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
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg(str`Update ${item.verboseName}`)} </span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.pk,
                        }}
                        type=${ifDefined(item.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal model=${item.metaModelName} objectPk=${item.pk}>
                </ak-rbac-object-permission-modal>
                ${this.renderStageActions(item)}`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-stage-wizard></ak-stage-wizard> `;
    }
}
