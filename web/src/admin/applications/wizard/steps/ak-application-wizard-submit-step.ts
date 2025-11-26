import "#admin/applications/wizard/ak-wizard-title";

import { ApplicationWizardStep } from "../ApplicationWizardStep.js";
import { isApplicationTransactionValidationError, OneOfProvider } from "../types.js";
import { providerRenderers } from "./SubmitStepOverviewRenderers.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError } from "#common/errors/network";

import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { CustomEmitterElement } from "#elements/utils/eventEmitter";

import { WizardNavigationEvent } from "#components/ak-wizard/events";
import { type WizardButton } from "#components/ak-wizard/types";

import {
    type ApplicationRequest,
    CoreApi,
    instanceOfValidationError,
    type ModelRequest,
    type PolicyBinding,
    ProviderModelEnum,
    ProxyMode,
    type ProxyProviderRequest,
    type TransactionApplicationRequest,
    type TransactionApplicationResponse,
    type TransactionPolicyBindingRequest,
} from "@goauthentik/api";

import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

// import { map } from "lit/directives/map.js";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFProgressStepper from "@patternfly/patternfly/components/ProgressStepper/progress-stepper.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBullseye from "@patternfly/patternfly/layouts/Bullseye/bullseye.css";

const _submitStates = ["reviewing", "running", "submitted"] as const;
type SubmitStates = (typeof _submitStates)[number];

type StrictProviderModelEnum = Exclude<ProviderModelEnum, "11184809">;

const providerMap: Map<string, string> = Object.values(ProviderModelEnum)
    .filter((value) => /^authentik_providers_/.test(value) && /provider$/.test(value))
    .reduce((acc: Map<string, string>, value) => {
        acc.set(value.split(".")[1], value);
        return acc;
    }, new Map());

type NonEmptyArray<T> = [T, ...T[]];

type MaybeTemplateResult = TemplateResult | typeof nothing;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isNotEmpty = (arr: any): arr is NonEmptyArray<any> => Array.isArray(arr) && arr.length > 0;

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

    label = msg("Review and Submit Application");

    @state()
    state: SubmitStates = "reviewing";

    async send() {
        const app = this.wizard.app;
        const provider = this.wizard.provider as ModelRequest;

        if (app === undefined) {
            throw new Error("Reached the submit state with the app undefined");
        }

        if (provider === undefined) {
            throw new Error("Reached the submit state with the provider undefined");
        }

        // Stringly-based API. Not the best, but it works. Just be aware that it is
        // stringly-based.

        const providerModel = providerMap.get(this.wizard.providerModel) as StrictProviderModelEnum;
        provider.providerModel = providerModel;

        // Special case for the Proxy provider.
        if (this.wizard.providerModel === "proxyprovider") {
            (provider as ProxyProviderRequest).mode = this.wizard.proxyMode;
            if ((provider as ProxyProviderRequest).mode !== ProxyMode.ForwardDomain) {
                (provider as ProxyProviderRequest).cookieDomain = "";
            }
        }

        const request: TransactionApplicationRequest = {
            app: cleanApplication(this.wizard.app),
            providerModel,
            provider,
            policyBindings: (this.wizard.bindings ?? []).map(cleanBinding),
        };

        this.state = "running";

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

                this.handleUpdate({ errors: parsedError });
                this.state = "reviewing";
            });
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
                    `Submit step received incoherent button/state combination: ${[button.kind, state]}`,
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

    renderInfo(
        state: string,
        label: string,
        icons: string[],
        extraInfo: MaybeTemplateResult = nothing,
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

        return html`
            <div class="ak-wizard-main-content">
                <ak-wizard-title>${msg("Review the Application and Provider")}</ak-wizard-title>
                <h2 class="pf-c-title pf-m-xl">${msg("Application")}</h2>
                <dl class="pf-c-description-list">
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">${msg("Name")}</dt>
                        <dt class="pf-c-description-list__description">${app.name}</dt>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">${msg("Group")}</dt>
                        <dt class="pf-c-description-list__description">${app.group || msg("-")}</dt>
                    </div>
                    <div class="pf-c-description-list__group">
                        <dt class="pf-c-description-list__term">${msg("Policy engine mode")}</dt>
                        <dt class="pf-c-description-list__description">
                            ${app.policyEngineMode?.toUpperCase()}
                        </dt>
                    </div>
                    ${metaLaunchUrl
                        ? html` <div class="pf-c-description-list__group">
                              <dt class="pf-c-description-list__term">${msg("Launch URL")}</dt>
                              <dt class="pf-c-description-list__description">${metaLaunchUrl}</dt>
                          </div>`
                        : nothing}
                </dl>
                ${renderer
                    ? html` <h2 class="pf-c-title pf-m-xl pf-u-pt-xl">${msg("Provider")}</h2>
                          ${renderer(provider)}`
                    : nothing}
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
