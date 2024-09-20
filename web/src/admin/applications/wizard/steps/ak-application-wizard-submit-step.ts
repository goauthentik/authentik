import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { parseAPIError } from "@goauthentik/common/errors";
import { WizardNavigationEvent } from "@goauthentik/components/ak-wizard/events.js";
import { type WizardButton } from "@goauthentik/components/ak-wizard/types";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";
import { P, match } from "ts-pattern";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import {
    type ApplicationRequest,
    CoreApi,
    PolicyEngineMode,
    type TransactionApplicationRequest,
    type TransactionApplicationResponse,
    ValidationError,
} from "@goauthentik/api";

import { ApplicationWizardStep } from "../ApplicationWizardStep.js";
import { OneOfProvider } from "../types.js";
import { type ProviderModelType, providerModelsList } from "./ProviderChoices.js";
import { providerRenderers } from "./SubmitStepOverviewRenderers.js";

const _submitStates = ["reviewing", "running", "submitted"] as const;
type SubmitStates = (typeof _submitStates)[number];

type NonEmptyArray<T> = [T, ...T[]];

type ExtendedValidationError = ValidationError & {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    app?: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    provider?: any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    detail?: any;
};

const JSON_INDENT = 2;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const errStr = (o: any) => JSON.stringify(o, null, JSON_INDENT);

function cleanApplication(app: Partial<ApplicationRequest>): ApplicationRequest {
    return {
        name: "",
        slug: "",
        ...app,
    };
}

@customElement("ak-application-wizard-submit-step")
export class ApplicationWizardSubmitStep extends CustomEmitterElement(ApplicationWizardStep) {
    static get styles() {
        return [...ApplicationWizardStep.styles, PFDescriptionList];
    }

    label = msg("Review and Submit Application");

    @state()
    state: SubmitStates = "reviewing";

    @state()
    errors?: ValidationError;

    async send() {
        const app = this.wizard.app;
        const provider = this.wizard.provider;
        if (app === undefined) {
            throw new Error("Reached the submit state with the app undefined");
        }

        if (provider === undefined) {
            throw new Error("Reached the submit state with the provider undefined");
        }

        const request: TransactionApplicationRequest = {
            providerModel: this.currentProviderModel.modelName as ProviderModelType,
            app: cleanApplication(app),
            provider: this.currentProviderModel.converter(provider),
        };

        this.errors = undefined;
        this.state = "running";

        return (
            new CoreApi(DEFAULT_CONFIG)
                .coreTransactionalApplicationsUpdate({
                    transactionApplicationRequest: request,
                })
                .then((_response: TransactionApplicationResponse) => {
                    this.dispatchCustomEvent(EVENT_REFRESH);
                    this.state = "submitted";
                })

                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                .catch(async (resolution: any) => {
                    this.errors = await parseAPIError(resolution);
                    this.state = "reviewing";
                })
        );
    }

    override handleButton(button: WizardButton) {
        match([button.kind, this.state])
            .with([P.union("back", "cancel"), P._], () => {
                super.handleButton(button);
            })
            .with(["close", "submitted"], () => {
                super.handleButton(button);
            })
            .with(["next", "reviewing"], () => {
                this.send();
            })
            .with([P._, "running"], () => {
                throw new Error("No buttons should be showing when running submit phase");
            })
            .otherwise(() => {
                throw new Error(
                    `Submit step received incoherent button/state combination: ${[button.kind, state]}`
                );
            });
    }

    get buttons(): WizardButton[] {
        const forReview: WizardButton[] = [
            { kind: "next", label: msg("Submit"), destination: "here" },
            { kind: "back", destination: "bindings" },
            { kind: "cancel" },
        ];

        const forSubmit: WizardButton[] = [{ kind: "close" }];

        return match(this.state)
            .with("submitted", () => forSubmit)
            .with("running", () => [])
            .with("reviewing", () => forReview)
            .exhaustive();
    }

    get currentProviderModel() {
        const providerModel = providerModelsList.find(
            ({ formName }) => formName === this.wizard.providerModel
        );
        if (!providerModel) {
            throw new Error(
                `Could not determine provider model from user request: ${errStr(this.wizard)}`
            );
        }
        return providerModel;
    }

    renderSuccess() {
        return this.renderInfo("success", msg("Your application has been saved"), [
            "fa-check-circle",
            "pf-m-success",
        ]);
    }

    renderRunning() {
        return this.renderInfo("running", msg("Saving application..."), ["fa-cogs", "pf-m-info"]);
    }

    renderInfo(state: string, label: string, icon: string[]) {
        return html`<div data-ouid-component-state=${this.state}>
            <div class="pf-l-bullseye">
                <div class="pf-c-empty-state pf-m-lg">
                    <div class="pf-c-empty-state__content">
                        <i class="fas fa- ${icon} pf-c-empty-state__icon" aria-hidden="true"></i>
                        <h1 data-ouia-commit-state=${state} class="pf-c-title pf-m-lg">${label}</h1>
                    </div>
                </div>
            </div>
        </div>`;
    }

    renderErrors(errors?: ValidationError) {
        if (!errors) {
            return nothing;
        }

        const navTo = (step: string) => () => this.dispatchEvent(new WizardNavigationEvent(step));

        return html` <hr class="pf-c-divider" />
            <h3>${msg("There was a problem saving your application.")}</h3>
            ${match(errors as ExtendedValidationError)
                .with(
                    { app: P.nonNullable },
                    () =>
                        html`<p>${msg("There was an error in the application.")}</p>
                            <p>
                                <a @click=${navTo("application")}
                                    >${msg("Review the application.")}</a
                                >
                            </p>`
                )
                .with(
                    { provider: P.nonNullable },
                    () =>
                        html`<p>${msg("There was an error in the provider.")}</p>
                            <p>
                                <a @click=${navTo("provider")}>${msg("Review the provider.")}</a>
                            </p>`
                )
                .with(
                    { detail: P.nonNullable },
                    () =>
                        `<p>${msg("There was an error. Please go back and review the application.")}: ${errors.detail}</p>`
                )
                .with(
                    {
                        nonFieldErrors: P.when(
                            (nonFieldErrors: string[]): nonFieldErrors is NonEmptyArray<string> =>
                                nonFieldErrors.length > 0
                        ),
                    },
                    () =>
                        html`<p>${msg("There was an error:")}:</p>
                            <ul>
                                ${(errors.nonFieldErrors ?? []).map(
                                    (e: string) => html`<li>${e}</li>`
                                )}
                            </ul>
                            <p>${msg("Please go back and review the application.")}</p>`
                )
                .otherwise(
                    () =>
                        html`<p>
                            ${msg(
                                "There was an error creating the application, but no error message was sent. Please review the server logs."
                            )}
                        </p>`
                )}`;
    }

    renderReview(app: Partial<ApplicationRequest>, provider: OneOfProvider) {
        const renderer = providerRenderers.get(this.currentProviderModel.modelName);
        return html`<h2 class="pf-c-title pf-m-xl">${msg("Application")}</h2>
            <dl class="pf-c-description-list">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">Name</dt>
                    <dt class="pf-c-description-list__description">${app.name}</dt>
                </div>
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__description">
                        ${msg("Policy Engine Mode:")}:
                        <strong
                            >${app.policyEngineMode === PolicyEngineMode.Any
                                ? msg("Any")
                                : msg("All")}</strong
                        >
                    </dt>
                </div>
                ${(app.metaLaunchUrl ?? "").trim() !== ""
                    ? html` <div class="pf-c-description-list__group">
                          <dt class="pf-c-description-list__term">Launch URL</dt>
                          <dt class="pf-c-description-list__description">${app.metaLaunchUrl}</dt>
                      </div>`
                    : nothing}
            </dl>
            ${renderer
                ? html` <h2 class="pf-c-title pf-m-xl pf-u-pt-xl">${msg("Provider")}</h2>
                      ${renderer(provider)}`
                : nothing}
            ${this.renderErrors()} `;
    }

    renderMain() {
        const app = this.wizard.app;
        const provider = this.wizard.provider;
        if (!(this.wizard && app && provider)) {
            throw new Error("Submit step received uninitialized wizard context");
        }
        return match(this.state)
            .with("submitted", () => this.renderSuccess())
            .with("running", () => this.renderRunning())
            .with("reviewing", () => this.renderReview(app, provider))
            .exhaustive();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-submit-step": ApplicationWizardSubmitStep;
    }
}
