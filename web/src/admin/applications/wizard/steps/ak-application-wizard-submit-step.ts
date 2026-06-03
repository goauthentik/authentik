import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError } from "#common/errors/network";

import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { CustomEmitterElement } from "#elements/utils/eventEmitter";

import { WizardNavigationEvent } from "#components/ak-wizard/events";
import { type WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import {
    isApplicationTransactionValidationError,
    OneOfProvider,
} from "#admin/applications/wizard/steps/providers/shared";
import { providerRenderers } from "#admin/applications/wizard/steps/SubmitStepOverviewRenderers";

import {
    type ApplicationRequest,
    CoreApi,
    instanceOfValidationError,
    type ModelRequest,
    PoliciesApi,
    type PolicyBinding,
    ProviderModelEnum,
    ProvidersApi,
    type ProvidersSamlImportMetadataCreateRequest,
    ProxyMode,
    type ProxyProviderRequest,
    type TransactionApplicationRequest,
    type TransactionApplicationResponse,
    type TransactionPolicyBindingRequest,
} from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFProgressStepper from "@patternfly/patternfly/components/ProgressStepper/progress-stepper.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";

const _submitStates = ["reviewing", "running", "submitted"] as const;
type SubmitStates = (typeof _submitStates)[number];

type StrictProviderModelEnum = Exclude<ProviderModelEnum, "11184809">;

const providerMap: Map<string, StrictProviderModelEnum> = Object.values(ProviderModelEnum)
    .filter((value): value is StrictProviderModelEnum => {
        return /^authentik_providers_/.test(value) && /provider$/.test(value);
    })
    .reduce((acc: Map<string, StrictProviderModelEnum>, value) => {
        const key = value.split(".")[1];
        acc.set(key, value);

        return acc;
    }, new Map());

type NonEmptyArray<T> = [T, ...T[]];

function isNotEmpty<T>(arr: T[] | undefined): arr is NonEmptyArray<T> {
    return Array.isArray(arr) && arr.length > 0;
}

const cleanApplication = (app: Partial<ApplicationRequest>): ApplicationRequest => ({
    name: "",
    slug: "",
    ...app,
});

const cleanBinding = (binding: PolicyBinding): TransactionPolicyBindingRequest => ({
    policy: binding.policy,
    group: binding.group,
    user: binding.user,
    negate: binding.negate,
    enabled: binding.enabled,
    order: binding.order,
    timeout: binding.timeout,
    failureResult: binding.failureResult,
});

@customElement("ak-application-wizard-submit-step")
export class ApplicationWizardSubmitStep extends CustomEmitterElement(ApplicationWizardStep) {
    static styles = [
        ...ApplicationWizardStep.styles,
        PFBullseye,
        PFEmptyState,
        PFTitle,
        PFProgressStepper,
        PFDescriptionList,
        css`
            .ak-wizard-main-content .pf-c-title {
                padding-bottom: var(--pf-global--spacer--md);
                padding-top: var(--pf-global--spacer--md);
            }
        `,
    ];

    public override label = msg("Review and Submit Application");

    @state()
    protected state: SubmitStates = "reviewing";

    async sendSAMLMetadataImport() {
        const providerData = this.wizard.provider as ProvidersSamlImportMetadataCreateRequest;
        const providersApi = new ProvidersApi(DEFAULT_CONFIG);
        const coreApi = new CoreApi(DEFAULT_CONFIG);
        const policiesApi = new PoliciesApi(DEFAULT_CONFIG);

        try {
            // Step 1: Import SAML metadata to create the provider
            const createdProvider = await providersApi.providersSamlImportMetadataCreate({
                file: providerData.file,
                name: providerData.name,
                authorizationFlow: providerData.authorizationFlow || "",
                invalidationFlow: providerData.invalidationFlow || "",
            });

            // Step 2: Create the application linked to the provider
            const appData = cleanApplication(this.wizard.app);
            appData.provider = createdProvider.pk;

            const createdApp = await coreApi.coreApplicationsCreate({
                applicationRequest: appData,
            });

            // Step 3: Create policy bindings
            for (const binding of this.wizard.bindings ?? []) {
                const bindingData = cleanBinding(binding);
                await policiesApi.policiesBindingsCreate({
                    policyBindingRequest: {
                        ...bindingData,
                        target: createdApp.pk,
                    },
                });
            }

            this.dispatchCustomEvent(EVENT_REFRESH);
            this.state = "submitted";
        } catch (error) {
            const parsedError = await parseAPIResponseError(error);

            if (!instanceOfValidationError(parsedError)) {
                showAPIErrorMessage(parsedError);
                this.state = "reviewing";
                return;
            }

            this.dispatchEvents({ update: { errors: parsedError } });
            this.state = "reviewing";
        }
    }

    async send() {
        const app = this.wizard.app;
        const provider = this.wizard.provider as ModelRequest;

        if (!app) {
            throw new Error("Reached the submit state without the application initialized");
        }

        if (!provider) {
            throw new Error("Reached the submit state without the provider initialized");
        }

        this.state = "running";

        // Special case for SAML metadata import - use a two-step process
        if (this.wizard.providerModel === "samlproviderimportmodel") {
            return this.sendSAMLMetadataImport();
        }

        // Stringly-based API. Not the best, but it works. Just be aware that it is
        // stringly-based.

        const providerModel = providerMap.get(this.wizard.providerModel);

        if (!providerModel) {
            throw new TypeError("Unrecognized provider model: " + this.wizard.providerModel);
        }

        provider.providerModel = providerModel;

        // Special case for the Proxy provider.
        if (this.wizard.providerModel === "proxyprovider") {
            const proxyProviderRequest = provider as ProxyProviderRequest;
            proxyProviderRequest.mode = this.wizard.proxyMode;

            if (proxyProviderRequest.mode !== ProxyMode.ForwardDomain) {
                proxyProviderRequest.cookieDomain = "";
            }
        }

        const request: TransactionApplicationRequest = {
            app: cleanApplication(this.wizard.app),
            providerModel,
            provider,
            policyBindings: (this.wizard.bindings ?? []).map(cleanBinding),
        };

        return new CoreApi(DEFAULT_CONFIG)
            .coreTransactionalApplicationsUpdate({
                transactionApplicationRequest: request,
            })
            .then((_response: TransactionApplicationResponse) => {
                this.dispatchCustomEvent(EVENT_REFRESH);
                this.state = "submitted";
            })

            .catch(async (error) => {
                const parsedError = await parseAPIResponseError(error);

                if (!instanceOfValidationError(parsedError)) {
                    showAPIErrorMessage(parsedError);

                    return;
                }

                if (isApplicationTransactionValidationError(parsedError)) {
                    // THIS is a really gross special case; if the user is duplicating the name of an existing provider, the error appears on the `app` (!) error object.
                    // We have to move that to the `provider.name` error field so it shows up in the right place.
                    if (Array.isArray(parsedError.app?.provider)) {
                        const providerError = parsedError.app.provider;

                        parsedError.provider = {
                            ...parsedError.provider,
                            name: providerError,
                        };

                        delete parsedError.app.provider;

                        if (Object.keys(parsedError.app).length === 0) {
                            delete parsedError.app;
                        }
                    }
                }

                this.dispatchEvents({ update: { errors: parsedError } });
                this.state = "reviewing";
            });
    }

    public override handleButton(button: WizardButton) {
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
                    `Submit step received incoherent button/state combination: ${[button.kind, state]}`,
                );
            });
    }

    protected get buttons(): WizardButton[] {
        return match(this.state)
            .with("submitted", () => {
                return [
                    { kind: "close" },
                    { kind: "finish", destination: "close" },
                ] satisfies WizardButton[];
            })
            .with("reviewing", () => {
                return [
                    { kind: "cancel" },
                    { kind: "back", destination: "bindings" },
                    { kind: "next", label: msg("Create Application"), destination: "here" },
                ] satisfies WizardButton[];
            })
            .with("running", () => [])
            .exhaustive();
    }

    renderInfo(
        state: string,
        label: string,
        icons: string[],
        extraInfo: SlottedTemplateResult = nothing,
    ) {
        const icon = classMap(icons.reduce((acc, icon) => ({ ...acc, [icon]: true }), {}));

        return html`<div data-ouid-component-state=${this.state} class="ak-wizard-main-content">
            <div class="pf-l-bullseye">
                <div class="pf-c-empty-state pf-m-lg">
                    <div class="pf-c-empty-state__content">
                        <i class="fas ${icon} pf-c-empty-state__icon" aria-hidden="true"></i>
                        <h1 data-ouia-commit-state=${state} class="pf-c-title pf-m-lg">${label}</h1>
                        ${extraInfo}
                    </div>
                </div>
            </div>
        </div>`;
    }

    renderError() {
        const { errors } = this.wizard;

        if (Object.keys(errors).length === 0) return nothing;

        return html` <hr class="pf-c-divider" />
            ${match(errors)
                .with(
                    { app: P.nonNullable },
                    () =>
                        html`<p>${msg("There was an error in the application.")}</p>
                            <p>
                                <a @click=${WizardNavigationEvent.toListener(this, "application")}>
                                    ${msg("Review the application.")}
                                </a>
                            </p>`,
                )
                .with(
                    { provider: P.nonNullable },
                    () =>
                        html`<p>${msg("There was an error in the provider.")}</p>
                            <p>
                                <a @click=${WizardNavigationEvent.toListener(this, "provider")}
                                    >${msg("Review the provider.")}</a
                                >
                            </p>`,
                )
                .with(
                    { detail: P.nonNullable },
                    () =>
                        html`<p>
                            ${msg(
                                "There was an error. Please go back and review the application.",
                            )}:
                            ${errors.detail}
                        </p>`,
                )
                .with(
                    {
                        nonFieldErrors: P.when(isNotEmpty),
                    },
                    () =>
                        html`<p>${msg("There was an error:")}:</p>
                            <ul>
                                ${(errors.nonFieldErrors ?? []).map(
                                    (reason) => html`<li>${reason}</li>`,
                                )}
                            </ul>
                            <p>${msg("Please go back and review the application.")}</p>`,
                )
                .otherwise(
                    () =>
                        html`<p>
                            ${msg(
                                "There was an error creating the application, but no error message was sent. Please review the server logs.",
                            )}
                        </p>`,
                )}`;
    }

    renderReview(app: Partial<ApplicationRequest>, provider: OneOfProvider) {
        const renderer = providerRenderers.get(this.wizard.providerModel);

        if (!renderer) {
            throw new Error(
                `Provider ${this.wizard.providerModel ?? "-- undefined --"} has no summary renderer.`,
            );
        }

        const metaLaunchUrl = app.metaLaunchUrl?.trim();

        return html`<h2 class="pf-c-wizard__main-title">
                    ${msg("Review the Application and Provider")}
                </h2>
                <fieldset class="ak-c-fieldset" name="application-details">
                    <legend>${msg("Application Details")}</legend>
                    <dl class="pf-c-description-list">
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">${msg("Application Name")}</dt>
                            <dt class="pf-c-description-list__description">${app.name}</dt>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">${msg("Group")}</dt>
                            <dt class="pf-c-description-list__description">
                                ${app.group || msg("-")}
                            </dt>
                        </div>
                        <div class="pf-c-description-list__group">
                            <dt class="pf-c-description-list__term">
                                ${msg("Policy engine mode")}
                            </dt>
                            <dt class="pf-c-description-list__description">
                                ${app.policyEngineMode?.toUpperCase()}
                            </dt>
                        </div>
                        ${
                            metaLaunchUrl
                                ? html`<div class="pf-c-description-list__group">
                                      <dt class="pf-c-description-list__term">
                                          ${msg("Launch URL")}
                                      </dt>
                                      <dt class="pf-c-description-list__description">
                                          ${metaLaunchUrl}
                                      </dt>
                                  </div>`
                                : nothing
                        }
                    </dl>
                </fieldset>

                ${
                    renderer
                        ? html`<fieldset class="ak-c-fieldset" name="provider-details">
                              <legend>${msg("Provider Details")}</legend>
                              ${renderer(provider)}
                          </fieldset>`
                        : null
                }
            </div>
        `;
    }

    renderMain() {
        const app = this.wizard.app;
        const provider = this.wizard.provider;
        if (!(this.wizard && app && provider)) {
            throw new Error("Submit step received uninitialized wizard context");
        }
        // An empty object is truthy, an empty array is falsey. *WAT JavaScript*.
        const keys = Object.keys(this.wizard.errors);
        return match([this.state, keys])
            .with(["submitted", P._], () =>
                this.renderInfo("success", msg("Your application has been saved"), [
                    "fa-check-circle",
                    "pf-m-success",
                ]),
            )
            .with(["running", P._], () =>
                this.renderInfo("running", msg("Saving application..."), ["fa-cogs", "pf-m-info"]),
            )
            .with(["reviewing", []], () => this.renderReview(app, provider))
            .with(["reviewing", [P.any, ...P.array()]], () =>
                this.renderInfo(
                    "error",
                    msg("authentik was unable to complete this process."),
                    ["fa-times-circle", "pf-m-danger"],
                    this.renderError(),
                ),
            )
            .exhaustive();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-submit-step": ApplicationWizardSubmitStep;
    }
}
