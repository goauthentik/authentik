import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { EmailStage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-email-form")
export class EmailStageForm extends ModelForm<EmailStage, string> {
    loadInstance(pk: string): Promise<EmailStage> {
        return new StagesApi(DEFAULT_CONFIG)
            .stagesEmailRetrieve({
                stageUuid: pk,
            })
            .then((stage) => {
                this.showConnectionSettings = !stage.useGlobalSettings;
                return stage;
            });
    }

    @property({ type: Boolean })
    showConnectionSettings = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
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
            <span slot="header"> ${msg("Connection settings")} </span>
            <div slot="body" class="pf-c-form">
                <ak-form-element-horizontal label=${msg("SMTP Host")} ?required=${true} name="host">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.host || "")}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("SMTP Port")} ?required=${true} name="port">
                    <input
                        type="number"
                        value="${first(this.instance?.port, 25)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("SMTP Username")} name="username">
                    <input
                        type="text"
                        value="${ifDefined(this.instance?.username || "")}"
                        class="pf-c-form-control"
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("SMTP Password")}
                    ?writeOnly=${this.instance !== undefined}
                    name="password"
                >
                    <input type="text" value="" class="pf-c-form-control" />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useTls">
                    <div class="pf-c-check">
                        <input
                            type="checkbox"
                            class="pf-c-check__input"
                            ?checked=${first(this.instance?.useTls, true)}
                        />
                        <label class="pf-c-check__label"> ${msg("Use TLS")} </label>
                    </div>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal name="useSsl">
                    <div class="pf-c-check">
                        <input
                            type="checkbox"
                            class="pf-c-check__input"
                            ?checked=${first(this.instance?.useSsl, false)}
                        />
                        <label class="pf-c-check__label"> ${msg("Use SSL")} </label>
                    </div>
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("Timeout")}
                    ?required=${true}
                    name="timeout"
                >
                    <input
                        type="number"
                        value="${first(this.instance?.timeout, 30)}"
                        class="pf-c-form-control"
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal
                    label=${msg("From address")}
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
                ${msg(
                    "Verify the user's email address by sending them a one-time-link. Can also be used for recovery to verify the user's authenticity.",
                )}
            </div>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal name="activateUserOnSuccess">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.activateUserOnSuccess, true)}
                            />
                            <label class="pf-c-check__label">
                                ${msg("Activate pending user on success")}
                            </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When a user returns from the email successfully, their account will be activated.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="useGlobalSettings">
                        <div class="pf-c-check">
                            <input
                                type="checkbox"
                                class="pf-c-check__input"
                                ?checked=${first(this.instance?.useGlobalSettings, true)}
                                @change=${(ev: Event) => {
                                    const target = ev.target as HTMLInputElement;
                                    this.showConnectionSettings = !target.checked;
                                }}
                            />
                            <label class="pf-c-check__label"> ${msg("Use global settings")} </label>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When enabled, global Email connection settings will be used and connection settings below will be ignored.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Token expiry")}
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
                            ${msg("Time in minutes the token sent is valid.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Subject")}
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
                        label=${msg("Template")}
                        ?required=${true}
                        name="template"
                    >
                        <select name="users" class="pf-c-form-control">
                            ${until(
                                new StagesApi(DEFAULT_CONFIG)
                                    .stagesEmailTemplatesList()
                                    .then((templates) => {
                                        return templates.map((template) => {
                                            const selected =
                                                this.instance?.template === template.name;
                                            return html`<option
                                                value=${ifDefined(template.name)}
                                                ?selected=${selected}
                                            >
                                                ${template.description}
                                            </option>`;
                                        });
                                    }),
                                html`<option>${msg("Loading...")}</option>`,
                            )}
                        </select>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            ${this.renderConnectionSettings()}
        </form>`;
    }
}
