import { EmailStage, EmailStageTemplateEnum, StagesApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { first } from "../../../utils";

@customElement("ak-stage-email-form")
export class EmailStageForm extends Form<EmailStage> {

    set stageUUID(value: string) {
        new StagesApi(DEFAULT_CONFIG).stagesEmailRead({
            stageUuid: value,
        }).then(stage => {
            this.stage = stage;
        });
    }

    @property({attribute: false})
    stage?: EmailStage;

    @property({type: Boolean})
    showConnectionSettings = false;

    getSuccessMessage(): string {
        if (this.stage) {
            return gettext("Successfully updated stage.");
        } else {
            return gettext("Successfully created stage.");
        }
    }

    send = (data: EmailStage): Promise<EmailStage> => {
        if (this.stage) {
            return new StagesApi(DEFAULT_CONFIG).stagesEmailUpdate({
                stageUuid: this.stage.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesEmailCreate({
                data: data
            });
        }
    };

    renderConnectionSettings(): TemplateResult {
        if (!this.showConnectionSettings) {
            return html``;
        }
        return html`<ak-form-group>
                <span slot="header">
                    ${gettext("Connection settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${gettext("SMTP Host")}
                        ?required=${true}
                        name="host">
                        <input type="text" value="${ifDefined(this.stage?.host || "")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("SMTP Port")}
                        ?required=${true}
                        name="port">
                        <input type="number" value="${first(this.stage?.port, 25)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("SMTP Username")}
                        ?required=${true}
                        name="username">
                        <input type="text" value="${ifDefined(this.stage?.username || "")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("SMTP Password")}
                        ?required=${true}
                        name="password">
                        <input type="text" value="${ifDefined(this.stage?.password || "")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="useTls">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.stage?.useTls || true}>
                            <label class="pf-c-check__label">
                                ${gettext("Use TLS")}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="useSsl">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.stage?.useSsl || true}>
                            <label class="pf-c-check__label">
                                ${gettext("Use SSL")}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Timeout")}
                        ?required=${true}
                        name="timeout">
                        <input type="number" value="${first(this.stage?.timeout, 30)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("From address")}
                        ?required=${true}
                        name="fromAddress">
                        <input type="text" value="${ifDefined(this.stage?.fromAddress || "system@authentik.local")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.stage?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${gettext("Stage-specific settings")}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="useGlobalSettings">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.stage?.useGlobalSettings || true} @change=${(ev: Event) => {
                                const target = ev.target as HTMLInputElement;
                                this.showConnectionSettings = !target.checked;
                            }}>
                            <label class="pf-c-check__label">
                                ${gettext("Use global settings")}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">${gettext("When enabled, global Email connection settings will be used and connection settings below will be ignored.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Token expiry")}
                        ?required=${true}
                        name="tokenExpiry">
                        <input type="number" value="${first(this.stage?.tokenExpiry, 30)}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${gettext("Time in minutes the token sent is valid.")}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Subject")}
                        ?required=${true}
                        name="subject">
                        <input type="text" value="${first(this.stage?.subject, "authentik")}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${gettext("Template")}
                        ?required=${true}
                        name="subject">
                        <select name="users" class="pf-c-form-control">
                            <option value=${EmailStageTemplateEnum.AccountConfirmationHtml} ?selected=${this.stage?.template === EmailStageTemplateEnum.AccountConfirmationHtml}>
                                ${gettext("Account confirmation")}
                            </option>
                            <option value=${EmailStageTemplateEnum.PasswordResetHtml} ?selected=${this.stage?.template === EmailStageTemplateEnum.PasswordResetHtml}>
                                ${gettext("Password reset")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderConnectionSettings()}
        </form>`;
    }

}
