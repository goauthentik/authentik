import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { Stage, StagesApi } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import { groupBy } from "../../utils";
import "./authenticator_duo/AuthenticatorDuoStageForm.ts";
import "./authenticator_sms/AuthenticatorSMSStageForm.ts";
import "./authenticator_static/AuthenticatorStaticStageForm.ts";
import "./authenticator_totp/AuthenticatorTOTPStageForm.ts";
import "./authenticator_validate/AuthenticatorValidateStageForm.ts";
import "./authenticator_webauthn/AuthenticateWebAuthnStageForm.ts";
import "./captcha/CaptchaStageForm.ts";
import "./consent/ConsentStageForm.ts";
import "./deny/DenyStageForm.ts";
import "./dummy/DummyStageForm.ts";
import "./email/EmailStageForm.ts";
import "./identification/IdentificationStageForm.ts";
import "./invitation/InvitationStageForm.ts";
import "./password/PasswordStageForm.ts";
import "./prompt/PromptStageForm.ts";
import "./user_delete/UserDeleteStageForm.ts";
import "./user_login/UserLoginStageForm.ts";
import "./user_logout/UserLogoutStageForm.ts";
import "./user_write/UserWriteStageForm.ts";

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
            html`${item.flowSet?.map((flow) => {
                return html`<a href="#/flow/flows/${flow.slug}">
                    <code>${flow.slug}</code>
                </a>`;
            })}`,
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

    renderToolbar(): TemplateResult {
        return html` <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(
                        new StagesApi(DEFAULT_CONFIG).stagesAllTypesList().then((types) => {
                            return types.map((type) => {
                                return html`<li>
                                    <ak-forms-modal>
                                        <span slot="submit"> ${t`Create`} </span>
                                        <span slot="header"> ${t`Create ${type.name}`} </span>
                                        <ak-proxy-form slot="form" type=${type.component}>
                                        </ak-proxy-form>
                                        <button slot="trigger" class="pf-c-dropdown__menu-item">
                                            ${type.name}<br />
                                            <small>${type.description}</small>
                                        </button>
                                    </ak-forms-modal>
                                </li>`;
                            });
                        }),
                        html`<ak-spinner></ak-spinner>`,
                    )}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }
}
