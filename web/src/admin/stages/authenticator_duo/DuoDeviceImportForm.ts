import "#elements/Divider";
import "#elements/buttons/ActionButton/index";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { ModalForm } from "#elements/forms/ModalForm";
import { ModelForm } from "#elements/forms/ModelForm";
import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import {
    AuthenticatorDuoStage,
    AuthenticatorDuoStageManualDeviceImportRequest,
    CoreApi,
    CoreUsersListRequest,
    StagesApi,
    User,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-stage-authenticator-duo-device-import-form")
export class DuoDeviceImportForm extends ModelForm<AuthenticatorDuoStage, string> {
    public static override verboseName = msg("Duo Device");
    public static override verboseNamePlural = msg("Duo Devices");
    public static override createLabel = msg("Import");
    public static override submitVerb = msg("Import");
    public static override modifierLabel = msg("Import");
    public static override saveLabel = msg("Import");
    public static override submittingVerb = msg("Importing");

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

    protected override renderForm(): SlottedTemplateResult {
        return html` ${this.instance?.adminIntegrationKey !== ""
            ? this.renderFormAutomatic()
            : nothing}
        ${this.renderFormManual()}`;
    }

    protected renderFormManual(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} required name="username">
                <ak-search-select
                    placeholder=${msg("Select a user...")}
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
            <ak-text-input
                label=${msg("Duo User ID")}
                required
                name="duoUserId"
                placeholder=${msg("Type the Duo user ID for this device...")}
                autocomplete="off"
                input-hint="code"
                help=${msg("The user ID in Duo, can be found in the URL after clicking on a user.")}
            >
            </ak-text-input>`;
    }

    renderFormAutomatic(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Automatic import")}>
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
            <br /> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-authenticator-duo-device-import-form": DuoDeviceImportForm;
    }
}
