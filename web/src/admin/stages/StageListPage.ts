import "#admin/rbac/ObjectPermissionModal";
import "#admin/stages/StageWizard";
import "#admin/stages/authenticator_duo/AuthenticatorDuoStageForm";
import "#admin/stages/authenticator_duo/DuoDeviceImportForm";
import "#admin/stages/authenticator_email/AuthenticatorEmailStageForm";
import "#admin/stages/authenticator_endpoint_gdtc/AuthenticatorEndpointGDTCStageForm";
import "#admin/stages/authenticator_sms/AuthenticatorSMSStageForm";
import "#admin/stages/authenticator_static/AuthenticatorStaticStageForm";
import "#admin/stages/authenticator_totp/AuthenticatorTOTPStageForm";
import "#admin/stages/authenticator_validate/AuthenticatorValidateStageForm";
import "#admin/stages/authenticator_webauthn/AuthenticatorWebAuthnStageForm";
import "#admin/stages/captcha/CaptchaStageForm";
import "#admin/stages/consent/ConsentStageForm";
import "#admin/stages/deny/DenyStageForm";
import "#admin/stages/dummy/DummyStageForm";
import "#admin/stages/email/EmailStageForm";
import "#admin/stages/endpoint/EndpointStageForm";
import "#admin/stages/identification/IdentificationStageForm";
import "#admin/stages/invitation/InvitationStageForm";
import "#admin/stages/mtls/MTLSStageForm";
import "#admin/stages/password/PasswordStageForm";
import "#admin/stages/prompt/PromptStageForm";
import "#admin/stages/redirect/RedirectStageForm";
import "#admin/stages/source/SourceStageForm";
import "#admin/stages/user_delete/UserDeleteStageForm";
import "#admin/stages/user_login/UserLoginStageForm";
import "#admin/stages/user_logout/UserLogoutStageForm";
import "#admin/stages/user_write/UserWriteStageForm";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { Stage, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    public pageTitle = msg("Stages");
    public pageDescription = msg(
        "Stages are single steps of a Flow that a user is guided through. A stage can only be executed from within a flow.",
    );
    public pageIcon = "pf-icon pf-icon-plugged";
    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Flows")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

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

    renderStageActions(stage: Stage) {
        return stage.component === "ak-stage-authenticator-duo-form"
            ? html`<ak-forms-modal>
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
              </ak-forms-modal>`
            : nothing;
    }

    row(item: Stage): SlottedTemplateResult[] {
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
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg(str`Update ${item.verboseName}`)}</span>
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
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal model=${item.metaModelName} objectPk=${item.pk}>
                </ak-rbac-object-permission-modal>
                ${this.renderStageActions(item)}
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-stage-wizard></ak-stage-wizard> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-list": StageListPage;
    }
}
