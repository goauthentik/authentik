import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { EmailStage, StagesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-stage-email-form")
export class EmailStageForm extends ModelForm<EmailStage, string> {
    async loadInstance(pk: string): Promise<EmailStage> {
        const stage = await new StagesApi(DEFAULT_CONFIG).stagesEmailRetrieve({
            stageUuid: pk,
        });
        this.showConnectionSettings = !stage.useGlobalSettings;
        return stage;
    }

    async load(): Promise<void> {
        this.templates = await new StagesApi(DEFAULT_CONFIG).stagesEmailTemplatesList();
    }

    templates?: TypeCreate[];

    @property({ type: Boolean })
    showConnectionSettings = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: EmailStage): Promise<EmailStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesEmailPartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedEmailStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesEmailCreate({
                emailStageRequest: data,
            });
        }
    };

    renderConnectionSettings(): TemplateResult {
        if (!this.showConnectionSettings) {
            return html``;
        }
        return html`<ak-form-group>
            <span slot="header"> ${t`Connection settings`} </span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal label=${t`SMTP Host`} ?required=${true} name="host">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.host || "")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${t`SMTP Port`} ?required=${true} name="port">
                    <input
                        type="number"
                        value="${first(this.instance?.port, 25)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${t`SMTP Username`} name="username">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.username || "")}"
                        class="pf-c-form-control"
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${t`SMTP Password`}
                    ?writeOnly=${this.instance !== undefined}
                    name="password"
                >
                    <input type="text" value="" class="pf-c-form-control" />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useTls">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${first(this.instance?.useTls, true)}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${t`Use TLS`}</span>
                    </label>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useSsl">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${first(this.instance?.useSsl, false)}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${t`Use SSL`}</span>
                    </label>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${t`Timeout`} ?required=${true} name="timeout">
                    <input
                        type="number"
                        value="${first(this.instance?.timeout, 30)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${t`From address`}
                    ?required=${true}
                    name="fromAddress"
                >
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.fromAddress || "system@authentik.local")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
            </div>
        </ak-form-group>`;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Verify the user's email address by sending them a one-time-link. Can also be used for recovery to verify the user's authenticity.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Stage-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="activateUserOnSuccess">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.activateUserOnSuccess, true)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label"
                                >${t`Activate pending user on success`}</span
                            >
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`When a user returns from the email successfully, their account will be activated.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="useGlobalSettings">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.useGlobalSettings, true)}
                                @change=${(ev: Event) => {
                                    const target = ev.target as HTMLInputElement;
                                    this.showConnectionSettings = !target.checked;
                                }}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${t`Use global settings`}</span>
                        </label>
                        <p class="pf-c-form__helper-text">
                            ${t`When enabled, global Email connection settings will be used and connection settings below will be ignored.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Token expiry`}
                        ?required=${true}
                        name="tokenExpiry"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.tokenExpiry, 30)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Time in minutes the token sent is valid.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Subject`}
                        ?required=${true}
                        name="subject"
                    >
                        <input
                            type="text"
                            value="${first(this.instance?.subject, "authentik")}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Template`}
                        ?required=${true}
                        name="template"
                    >
                        <select name="users" class="pf-c-form-control">
                            ${this.templates?.map((template) => {
                                const selected = this.instance?.template === template.name;
                                return html`<option
                                    value=${ifDefined(template.name)}
                                    ?selected=${selected}
                                >
                                    ${template.description}
                                </option>`;
                            })}
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderConnectionSettings()}
        </form>`;
    }
}
