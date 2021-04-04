import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/SpinnerButton";
import "../../elements/buttons/Dropdown";
import "../../elements/forms/DeleteForm";
import "../../elements/forms/ProxyForm";
import "../../elements/forms/ModalForm";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { Stage, StagesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

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
        return t`Stages are single steps of a Flow that a user is guided through.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-plugged";
    }
    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "name";

    apiEndpoint(page: number): Promise<AKResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Flows`),
            new TableColumn(""),
        ];
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
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${t`Update`}
                </span>
                <span slot="header">
                    ${t`Update ${item.verboseName}`}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "stageUUID": item.pk
                    }}
                    type=${ifDefined(item.component)}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${t`Edit`}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${item.verboseName || ""}
                .delete=${() => {
                    return new StagesApi(DEFAULT_CONFIG).stagesAllDelete({
                        stageUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${t`Delete`}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${t`Create`}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(new StagesApi(DEFAULT_CONFIG).stagesAllTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-forms-modal>
                                <span slot="submit">
                                    ${t`Create`}
                                </span>
                                <span slot="header">
                                    ${t`Create ${type.name}`}
                                </span>
                                <ak-proxy-form
                                    slot="form"
                                    type=${type.component}>
                                </ak-proxy-form>
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                            </ak-forms-modal>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

}
