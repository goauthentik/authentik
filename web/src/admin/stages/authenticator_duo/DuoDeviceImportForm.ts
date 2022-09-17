import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import "@goauthentik/elements/Divider";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModalForm } from "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import { UserOption } from "@goauthentik/elements/user/utils";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import {
    AuthenticatorDuoStage,
    CoreApi,
    StagesApi,
    StagesAuthenticatorDuoImportDeviceManualCreateRequest,
} from "@goauthentik/api";

@customElement("ak-stage-authenticator-duo-device-import-form")
export class DuoDeviceImportForm extends ModelForm<AuthenticatorDuoStage, string> {
    loadInstance(pk: string): Promise<AuthenticatorDuoStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return msg("Successfully imported device.");
    }

    send = (data: AuthenticatorDuoStage): Promise<void> => {
        const importData = data as unknown as StagesAuthenticatorDuoImportDeviceManualCreateRequest;
        importData.stageUuid = this.instancePk;
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoImportDeviceManualCreate(
            importData,
        );
    };

    renderForm(): TemplateResult {
        return html`${this.instance?.adminIntegrationKey !== ""
            ? this.renderFormAutomatic()
            : html``}
        ${this.renderFormManual()}`;
    }

    renderFormManual(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("User")} ?required=${true} name="username">
                <select class="pf-c-form-control">
                    ${until(
                        new CoreApi(DEFAULT_CONFIG)
                            .coreUsersList({
                                ordering: "username",
                            })
                            .then((users) => {
                                return users.results.map((user) => {
                                    return html`<option value=${user.username}>
                                        ${UserOption(user)}
                                    </option>`;
                                });
                            }),
                        html`<option>${msg("Loading...")}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("The user in authentik this device will be assigned to.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Duo User ID")}
                ?required=${true}
                name="duoUserId"
            >
                <input type="text" class="pf-c-form-control" required />
                <p class="pf-c-form__helper-text">
                    ${msg("The user ID in Duo.")}
                    ${msg(
                        "Can be either the username (found in the Users list) or the ID (can be found in the URL after clicking on a user).",
                    )}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

    renderFormAutomatic(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${msg("Automatic import")}>
                    <ak-action-button
                        class="pf-m-primary"
                        .apiRequest=${() => {
                            return new StagesApi(DEFAULT_CONFIG)
                                .stagesAuthenticatorDuoImportDevicesAutomaticCreate({
                                    stageUuid: this.instance?.pk || "",
                                })
                                .then((res) => {
                                    showMessage({
                                        level: MessageLevel.info,
                                        message: msg(
                                            str`Successfully imported ${res.count} devices.`,
                                        ),
                                    });
                                    const modal = this.parentElement as ModalForm;
                                    modal.open = false;
                                });
                        }}
                    >
                        ${msg("Start automatic import")}
                    </ak-action-button>
                </ak-form-element-horizontal>
            </form>
            <ak-divider>${msg("Or manually import")}</ak-divider>
            <br />
        `;
    }
}
