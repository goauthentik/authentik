import { AuthenticatorValidateStage, NotConfiguredActionEnum, DeviceClassesEnum, StagesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";
import { ModelForm } from "../../../elements/forms/ModelForm";

@customElement("ak-stage-authenticator-validate-form")
export class AuthenticatorValidateStageForm extends ModelForm<AuthenticatorValidateStage, string> {

    loadInstance(pk: string): Promise<AuthenticatorValidateStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateRetrieve({
            stageUuid: pk,
        }).then(stage => {
            this.showConfigureFlow = stage.notConfiguredAction === NotConfiguredActionEnum.Configure;
            return stage;
        });
    }

    @property({ type: Boolean })
    showConfigureFlow = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated stage.`;
        } else {
            return t`Successfully created stage.`;
        }
    }

    send = (data: AuthenticatorValidateStage): Promise<AuthenticatorValidateStage> => {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateUpdate({
                stageUuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorValidateCreate({
                data: data
            });
        }
    };

    isDeviceClassSelected(field: DeviceClassesEnum): boolean {
        return (this.instance?.deviceClasses || []).filter(isField => {
            return field === isField;
        }).length > 0;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Stage used to validate any authenticator. This stage should be used during authentication or authorization flows.`}
            </div>
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.instance?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Stage-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Not configured action`}
                        ?required=${true}
                        name="notConfiguredAction">
                        <select class="pf-c-form-control" @change=${(ev: Event) => {
                            const target = ev.target as HTMLSelectElement;
                            if (target.selectedOptions[0].value === NotConfiguredActionEnum.Configure) {
                                this.showConfigureFlow = true;
                            } else {
                                this.showConfigureFlow = false;
                            }
                        }}>
                            <option value=${NotConfiguredActionEnum.Configure} ?selected=${this.instance?.notConfiguredAction === NotConfiguredActionEnum.Configure}>
                                ${t`Force the user to configure an authenticator`}
                            </option>
                            <option value=${NotConfiguredActionEnum.Deny} ?selected=${this.instance?.notConfiguredAction === NotConfiguredActionEnum.Deny}>
                                ${t`Deny the user access`}
                            </option>
                            <option value=${NotConfiguredActionEnum.Skip} ?selected=${this.instance?.notConfiguredAction === NotConfiguredActionEnum.Skip}>
                                ${t`Continue`}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`User fields`}
                        ?required=${true}
                        name="transports">
                        <select name="users" class="pf-c-form-control" multiple>
                            <option value=${DeviceClassesEnum.Static} ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Static)}>
                                ${t`Static Tokens`}
                            </option>
                            <option value=${DeviceClassesEnum.Totp} ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Totp)}>
                                ${t`TOTP Authenticators`}
                            </option>
                            <option value=${DeviceClassesEnum.Webauthn} ?selected=${this.isDeviceClassSelected(DeviceClassesEnum.Webauthn)}>
                                ${t`WebAuthn Authenticators`}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">${t`Device classes which can be used to authenticate.`}</p>
                        <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
                    </ak-form-element-horizontal>
                    ${this.showConfigureFlow ? html`
                    <ak-form-element-horizontal
                        label=${t`Configuration flow`}
                        ?required=${true}
                        name="configureFlow">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.configurationStage === undefined}>---------</option>
                            ${until(new StagesApi(DEFAULT_CONFIG).stagesAllList({
                                ordering: "pk",
                            }).then(stages => {
                                return stages.results.map(stage => {
                                    const selected = this.instance?.configurationStage === stage.pk;
                                    return html`<option value=${ifDefined(stage.pk)} ?selected=${selected}>${stage.name} (${stage.verboseName})</option>`;
                                });
                            }), html`<option>${t`Loading...`}</option>`)}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Stage used to configure Authenticator when user doesn't have any compatible devices. After this configuration Stage passes, the user is not prompted again.`}</p>
                    </ak-form-element-horizontal>
                    `: html``}
                </div>
            </ak-form-group>
        </form>`;
    }

}
