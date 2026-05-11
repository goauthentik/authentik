import "#admin/users/ServiceAccountForm";
import "#admin/users/UserForm";
import "#components/ak-hidden-text-input";
import "#components/ak-text-input";
import "#elements/wizard/FormWizardPage";
import "#elements/wizard/TypeCreateWizardPage";
import "#elements/wizard/Wizard";

import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { CreateWizard } from "#elements/wizard/CreateWizard";
import { TypeCreateWizardPageLayouts } from "#elements/wizard/TypeCreateWizardPage";
import { WizardPage } from "#elements/wizard/WizardPage";

import { ButtonKindLabelRecord } from "#components/ak-wizard/shared";

import { UserForm } from "#admin/users/UserForm";

import { TypeCreate, UserServiceAccountResponse, UserTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

const SERVICE_ACCOUNT_FORM_SLOT =
    `type-ak-user-service-account-form-${UserTypeEnum.ServiceAccount}` as const;
const SERVICE_ACCOUNT_RESULT_SLOT = `${SERVICE_ACCOUNT_FORM_SLOT}-result` as const;

const DEFAULT_USER_TYPES: TypeCreate[] = [
    {
        component: "ak-user-form",
        modelName: UserTypeEnum.Internal,
        name: msg("Internal User"),
        description: msg("Company employees with access to the full enterprise feature set."),
    },
    {
        component: "ak-user-form",
        modelName: UserTypeEnum.External,
        name: msg("External User"),
        description: msg(
            "External consultants or B2C customers without access to enterprise features.",
        ),
    },
    {
        component: "ak-user-service-account-form",
        modelName: UserTypeEnum.ServiceAccount,
        name: msg("Service Account"),
        description: msg("Machine-to-machine authentication or other automations."),
    },
];

export interface UserWizardState {
    [SERVICE_ACCOUNT_FORM_SLOT]?: UserServiceAccountResponse;
}

@customElement("ak-user-service-account-result-page")
export class ServiceAccountResultPage extends WizardPage<UserWizardState> {
    public static styles: CSSResult[] = [PFForm, PFFormControl];

    public override headline = msg("View Credentials");

    @state()
    protected result: UserServiceAccountResponse | null = null;

    public override activeCallback = async (): Promise<void> => {
        const result = this.host.state[SERVICE_ACCOUNT_FORM_SLOT];

        if (!result) {
            throw new TypeError("Expected service account creation result in wizard state.");
        }

        this.result = result;

        this.host.valid = true;
        this.host.cancelable = false;
    };

    public formatNextLabel(): SlottedTemplateResult | null {
        return ButtonKindLabelRecord.close();
    }

    public override nextCallback = async (): Promise<boolean> => true;

    protected override render(): SlottedTemplateResult {
        if (!this.result) {
            return null;
        }

        const { username, token } = this.result;

        return html`<h3 class="pf-c-wizard__main-title">${msg("Review Credentials")}</h3>
            <h4 class="pf-c-title pf-m-md">
                ${msg(
                    "Use the username and password below to authenticate. The password can be retrieved later on the Tokens page.",
                )}
            </h4>
            <form class="pf-c-form pf-m-horizontal">
                <ak-text-input
                    label=${msg("Username")}
                    value=${username}
                    input-hint="code"
                    readonly
                ></ak-text-input>
                <ak-hidden-text-input
                    label=${msg("Password")}
                    value="${token}"
                    input-hint="code"
                    readonly
                    .help=${msg(
                        "Valid for 360 days, after which the password will automatically rotate. You can copy the password from the Token List.",
                    )}
                ></ak-hidden-text-input>
            </form>`;
    }
}

@customElement("ak-user-wizard")
export class AKUserWizard extends CreateWizard {
    /**
     * Default path to assign to new users created via the wizard.
     */
    @property({ type: String, attribute: "default-path" })
    public defaultPath: string = "users";

    protected apiEndpoint(): Promise<TypeCreate[]> {
        return Promise.resolve(DEFAULT_USER_TYPES);
    }

    public static override verboseName = msg("User");
    public static override verboseNamePlural = msg("Users");
    public override layout = TypeCreateWizardPageLayouts.list;

    protected override selectSteps(type: TypeCreate, currentSteps: string[]): string[] {
        const { modelName } = type;
        const serviceAccount = modelName === UserTypeEnum.ServiceAccount;

        if (!serviceAccount) {
            return super.selectSteps(type, currentSteps);
        }

        return [
            // ---
            SERVICE_ACCOUNT_FORM_SLOT,
            SERVICE_ACCOUNT_RESULT_SLOT,
        ];
    }

    protected override renderWizardStep(type: TypeCreate): SlottedTemplateResult {
        if (type.modelName === UserTypeEnum.ServiceAccount) {
            return [
                super.renderWizardStep(type),
                html`<ak-user-service-account-result-page
                    slot=${SERVICE_ACCOUNT_RESULT_SLOT}
                ></ak-user-service-account-result-page>`,
            ];
        }

        return super.renderWizardStep(type);
    }

    protected override assembleFormProps(type: TypeCreate): LitPropertyRecord<UserForm | object> {
        if (type.modelName === UserTypeEnum.ServiceAccount) {
            return {};
        }

        const props: LitPropertyRecord<UserForm> = {
            userType: type.modelName as UserTypeEnum,
            defaultPath: this.defaultPath,
        };

        return props;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-wizard": AKUserWizard;
        "ak-user-service-account-result-page": ServiceAccountResultPage;
    }
}
