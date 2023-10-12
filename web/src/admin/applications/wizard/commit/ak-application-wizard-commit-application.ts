import { EVENT_REFRESH } from "@goauthentik/app/common/constants";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { TemplateResult, css, html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFProgressStepper from "@patternfly/patternfly/components/ProgressStepper/progress-stepper.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";

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

type State = {
    state: "idle" | "running" | "error" | "success";
    label: string | TemplateResult;
    icon: string[];
};

const idleState: State = {
    state: "idle",
    label: "",
    icon: ["fa-cogs", "pf-m-pending"],
};

const runningState: State = {
    state: "running",
    label: msg("Saving Application..."),
    icon: ["fa-cogs", "pf-m-info"],
};
const errorState: State = {
    state: "error",
    label: msg("Authentik was unable to save this application:"),
    icon: ["fa-times-circle", "pf-m-danger"],
};

const successState: State = {
    state: "success",
    label: msg("Your application has been saved"),
    icon: ["fa-check-circle", "pf-m-success"],
};

@customElement("ak-application-wizard-commit-application")
export class ApplicationWizardCommitApplication extends BasePanel {
    static get styles() {
        return [
            ...super.styles,
            PFBullseye,
            PFEmptyState,
            PFTitle,
            PFProgressStepper,
            css`
                .pf-c-title {
                    padding-bottom: var(--pf-global--spacer--md);
                }
            `,
        ];
    }

    @state()
    commitState: State = idleState;

    @state()
    errors: string[] = [];

    response?: TransactionApplicationResponse;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    willUpdate(_changedProperties: Map<string, any>) {
        if (this.commitState === idleState) {
            this.response = undefined;
            this.commitState = runningState;
            const providerModel = providerModelsList.find(
                ({ formName }) => formName === this.wizard.providerModel,
            );
            if (!providerModel) {
                throw new Error(
                    `Could not determine provider model from user request: ${JSON.stringify(
                        this.wizard,
                        null,
                        2,
                    )}`,
                );
            }

            const request: TransactionApplicationRequest = {
                providerModel: providerModel.modelName as ProviderModelType,
                app: cleanApplication(this.wizard.app),
                provider: providerModel.converter(this.wizard.provider),
            };

            this.send(request);
            return;
        }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    decodeErrors(body: Record<string, any>) {
        const spaceify = (src: Record<string, string>) =>
            Object.values(src).map((msg) => `\u00a0\u00a0\u00a0\u00a0${msg}`);

        let errs: string[] = [];
        if (body["app"] !== undefined) {
            errs = [...errs, msg("In the Application:"), ...spaceify(body["app"])];
        }
        if (body["provider"] !== undefined) {
            errs = [...errs, msg("In the Provider:"), ...spaceify(body["provider"])];
        }
        console.log(body, errs);
        return errs;
    }

    async send(
        data: TransactionApplicationRequest,
    ): Promise<TransactionApplicationResponse | void> {
        this.errors = [];

        new CoreApi(DEFAULT_CONFIG)
            .coreTransactionalApplicationsUpdate({
                transactionApplicationRequest: data,
            })
            .then((response: TransactionApplicationResponse) => {
                this.response = response;
                this.dispatchCustomEvent(EVENT_REFRESH);
                this.dispatchWizardUpdate({ status: "submitted" });
                this.commitState = successState;
            })
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            .catch((resolution: any) => {
                resolution.response.json().then(
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    (body: Record<string, any>) => {
                        this.errors = this.decodeErrors(body);
                    },
                );
                this.commitState = errorState;
            });
    }

    render(): TemplateResult {
        const icon = classMap(
            this.commitState.icon.reduce((acc, icon) => ({ ...acc, [icon]: true }), {}),
        );

        return html`
            <div>
                <div class="pf-l-bullseye">
                    <div class="pf-c-empty-state pf-m-lg">
                        <div class="pf-c-empty-state__content">
                            <i
                                class="fas fa- ${icon} pf-c-empty-state__icon"
                                aria-hidden="true"
                            ></i>
                            <h1
                                data-commit-state=${this.commitState.state}
                                class="pf-c-title pf-m-lg"
                            >
                                ${this.commitState.label}
                            </h1>
                            ${this.errors.length > 0
                                ? html`<ul>
                                      ${this.errors.map(
                                          (msg) => html`<li><code>${msg}</code></li>`,
                                      )}
                                  </ul>`
                                : nothing}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

export default ApplicationWizardCommitApplication;
