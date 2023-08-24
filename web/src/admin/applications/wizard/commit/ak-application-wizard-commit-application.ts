import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import {
    ApplicationRequest,
    CoreApi,
    TransactionApplicationRequest,
    TransactionApplicationResponse,
} from "@goauthentik/api";
import type { ModelRequest } from "@goauthentik/api";

import BasePanel from "../BasePanel";
import providerModelsList from "../auth-method-choice/ak-application-wizard-authentication-method-choice.choices";

function cleanApplication(app: Partial<ApplicationRequest>): ApplicationRequest {
    return {
        name: "",
        slug: "",
        ...app,
    };
}

type ProviderModelType = Exclude<ModelRequest["providerModel"], "11184809">;

@customElement("ak-application-wizard-commit-application")
export class ApplicationWizardCommitApplication extends BasePanel {
    state: "idle" | "running" | "done" = "idle";
    response?: TransactionApplicationResponse;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    willUpdate(_changedProperties: Map<string, any>) {
        if (this.state === "idle") {
            this.response = undefined;
            this.state = "running";
            const provider = providerModelsList.find(
                ({ formName }) => formName === this.wizard.providerModel,
            );
            if (!provider) {
                throw new Error(
                    `Could not determine provider model from user request: ${JSON.stringify(
                        this.wizard,
                        null,
                        2,
                    )}`,
                );
            }

            const request: TransactionApplicationRequest = {
                providerModel: provider.modelName as ProviderModelType,
                app: cleanApplication(this.wizard.app),
                provider: provider.converter(this.wizard.provider),
            };

            this.send(request);
            return;
        }
    }

    async send(
        data: TransactionApplicationRequest,
    ): Promise<TransactionApplicationResponse | void> {
        new CoreApi(DEFAULT_CONFIG)
            .coreTransactionalApplicationsUpdate({ transactionApplicationRequest: data })
            .then(
                (response) => {
                    this.response = response;
                    this.state = "done";
                },
                (error) => {
                    console.log(error);
                },
            );
    }

    render(): TemplateResult {
        return html`
            <div>
                <h3>Current result:</h3>
                <p>State: ${this.state}</p>
                <pre>${JSON.stringify(this.wizard, null, 2)}</pre>
                <p>Response:</p>
                <pre>${JSON.stringify(this.response, null, 2)}</pre>
            </div>
        `;
    }
}

export default ApplicationWizardCommitApplication;
