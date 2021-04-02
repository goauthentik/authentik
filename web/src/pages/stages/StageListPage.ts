import { gettext } from "django";
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

import "./pages/stages/authenticator_static/AuthenticatorStaticStageForm.ts";
import "./pages/stages/authenticator_totp/AuthenticatorTOTPStageForm.ts";
import "./pages/stages/authenticator_validate/AuthenticatorValidateStageForm.ts";
import "./pages/stages/authenticator_webauthn/AuthenticateWebAuthnStageForm.ts";
import "./pages/stages/captcha/CaptchaStageForm.ts";
import "./pages/stages/consent/ConsentStageForm.ts";
import "./pages/stages/deny/DenyStageForm.ts";
import "./pages/stages/dummy/DummyStageForm.ts";
import "./pages/stages/email/EmailStageForm.ts";
import "./pages/stages/identification/IdentificationStageForm.ts";
import "./pages/stages/invitation/InvitationStageForm.ts";
import "./pages/stages/password/PasswordStageForm.ts";
import "./pages/stages/prompt/PromptStageForm.ts";
import "./pages/stages/user_delete/UserDeleteStageForm.ts";
import "./pages/stages/user_login/UserLoginStageForm.ts";
import "./pages/stages/user_logout/UserLogoutStageForm.ts";
import "./pages/stages/user_write/UserWriteStageForm.ts";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    pageTitle(): string {
        return "Stages";
    }
    pageDescription(): string | undefined {
        return "Stages are single steps of a Flow that a user is guided through.";
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
            new TableColumn("Name", "name"),
            new TableColumn("Flows"),
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
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext(`Update ${item.verboseName}`)}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "stageUUID": item.pk
                    }}
                    type=${ifDefined(item.objectType)}
                    .typeMap=${{
                        "dummy": "ak-policy-dummy-form",
                        "eventmatcher": "ak-policy-event-matcher-form",
                        "expression": "ak-policy-expression-form",
                        "passwordexpiry": "ak-policy-password-expiry-form",
                        "haveibeenpwend": "ak-policy-hibp-form",
                        "password": "ak-policy-password-form",
                        "reputation": "ak-policy-reputation-form",
                    }}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Group")}
                .delete=${() => {
                    return new StagesApi(DEFAULT_CONFIG).stagesAllDelete({
                        stageUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${gettext("Create")}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(new StagesApi(DEFAULT_CONFIG).stagesAllTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-forms-modal>
                                <span slot="submit">
                                    ${gettext("Create")}
                                </span>
                                <span slot="header">
                                    ${gettext(`Create ${type.name}`)}
                                </span>
                                <ak-proxy-form
                                    slot="form"
                                    type=${type.component}>
                                </ak-proxy-form>
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

}
