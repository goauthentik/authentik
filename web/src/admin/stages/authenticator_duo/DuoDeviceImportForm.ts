import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import "@goauthentik/elements/Divider";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModalForm } from "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    AuthenticatorDuoStage,
    AuthenticatorDuoStageManualDeviceImportRequest,
    CoreApi,
    CoreUsersListRequest,
    StagesApi,
    User,
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

    async send(data: AuthenticatorDuoStage): Promise<void> {
        const importData = data as unknown as AuthenticatorDuoStageManualDeviceImportRequest;
        return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorDuoImportDeviceManualCreate({
            stageUuid: this.instance?.pk || "",
            authenticatorDuoStageManualDeviceImportRequest: importData,
        });
    }

    renderForm(): TemplateResult {
        return html` ${this.instance?.adminIntegrationKey !== ""
            ? this.renderFormAutomatic()
            : html``}
        ${this.renderFormManual()}`;
    }

    renderFormManual(): TemplateResult {
        return html`<ak-form-element-horizontal
                label=${msg("User")}
                ?required=${true}
                name="username"
            >
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): TemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): string | undefined => {
                        return user?.username;
                    }}
                >
                </ak-search-select>

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
                    ${msg("The user ID in Duo, can be found in the URL after clicking on a user.")}
                </p>
            </ak-form-element-horizontal>`;
    }

    renderFormAutomatic(): TemplateResult {
        return html`
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
                                    message: msg(str`Successfully imported ${res.count} devices.`),
                                });
                                const modal = this.parentElement as ModalForm;
                                modal.open = false;
                            });
                    }}
                >
                    ${msg("Start automatic import")}
                </ak-action-button>
            </ak-form-element-horizontal>
            <ak-divider>${msg("Or manually import")}</ak-divider>
            <br />
        `;
    }
}
