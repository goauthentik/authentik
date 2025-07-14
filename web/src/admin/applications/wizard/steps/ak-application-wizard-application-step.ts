import "#admin/applications/wizard/ak-wizard-title";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { ApplicationWizardStateUpdate, ValidationRecord } from "../types.js";

import { camelToSnake } from "#common/utils";

import { isSlug } from "#elements/router/utils";

import { type NavigableButton, type WizardButton } from "#components/ak-wizard/types";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { type ApplicationRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, query, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-wizard-application-step")
export class ApplicationWizardApplicationStep extends ApplicationWizardStep<
    Partial<ApplicationRequest>
> {
    label = msg("Application");

    @state()
    errors = new Map<string, string>();

    @query("form#applicationform")
    form!: HTMLFormElement;

    constructor() {
        super();
        // This is the first step. Ensure it is always enabled.
        this.enabled = true;
    }

    errorMessages(name: string) {
        return this.errors.has(name)
            ? [this.errors.get(name)]
            : (this.wizard.errors?.app?.[name] ??
                  this.wizard.errors?.app?.[camelToSnake(name)] ??
                  []);
    }

    get buttons(): WizardButton[] {
        return [{ kind: "next", destination: "provider-choice" }, { kind: "cancel" }];
    }

    public reportValidity() {
        this.errors = new Map();

        const name = this.formValues.name?.trim();
        const slug = this.formValues.slug?.trim();
        const metaLaunchUrl = this.formValues.metaLaunchUrl?.trim();

        if (!name) {
            this.errors.set("name", msg("An application name is required"));
        }

        if (!metaLaunchUrl || !URL.canParse(metaLaunchUrl)) {
            this.errors.set("metaLaunchUrl", msg("Not a valid URL"));
        }

        if (!slug || !isSlug(slug)) {
            this.errors.set("slug", msg("Not a valid slug"));
        }

        return this.errors.size === 0;
    }

    protected override dispatchButtonEvent(button: NavigableButton) {
        if (button.kind !== "next") {
            return super.dispatchButtonEvent(button);
        }

        if (!this.reportValidity()) {
            this.handleEnabling({
                disabled: ["provider-choice", "provider", "bindings", "submit"],
            });
            return;
        }

        const app = this.formValues;

        let payload: ApplicationWizardStateUpdate = {
            app: this.formValues,
            errors: this.removeErrors("app"),
        };

        if (app.name && (this.wizard.provider?.name ?? "").trim() === "") {
            payload = {
                ...payload,
                provider: { name: `Provider for ${app.name}` },
            };
        }

        this.handleUpdate(payload, button.destination, {
            enable: "provider-choice",
        });
    }

    renderForm(app: Partial<ApplicationRequest>, errors: ValidationRecord) {
        return html` <ak-wizard-title>${msg("Configure The Application")}</ak-wizard-title>
            <form id="applicationform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    value=${ifDefined(app.name)}
                    label=${msg("Name")}
                    required
                    ?invalid=${this.errors.has("name")}
                    .errorMessages=${errors.name ?? this.errorMessages("name")}
                    help=${msg("Application's display Name.")}
                ></ak-text-input>
                <ak-slug-input
                    name="slug"
                    value=${ifDefined(app.slug)}
                    label=${msg("Slug")}
                    required
                    ?invalid=${errors.slug ?? this.errors.has("slug")}
                    .errorMessages=${this.errorMessages("slug")}
                    help=${msg("Internal application name used in URLs.")}
                    input-hint="code"
                ></ak-slug-input>
                <ak-text-input
                    name="group"
                    value=${ifDefined(app.group)}
                    label=${msg("Group")}
                    .errorMessages=${errors.group ?? []}
                    help=${msg(
                        "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                    )}
                    input-hint="code"
                ></ak-text-input>
                <ak-radio-input
                    label=${msg("Policy engine mode")}
                    required
                    name="policyEngineMode"
                    .options=${policyEngineModes}
                    .value=${app.policyEngineMode}
                    .errorMessages=${errors.policyEngineMode ?? []}
                ></ak-radio-input>
                <ak-form-group aria-label=${msg("UI Settings")}>
                    <span slot="header"> ${msg("UI Settings")} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-text-input
                            name="metaLaunchUrl"
                            label=${msg("Launch URL")}
                            value=${ifDefined(app.metaLaunchUrl)}
                            ?invalid=${this.errors.has("metaLaunchUrl")}
                            .errorMessages=${errors.metaLaunchUrl ??
                            this.errorMessages("metaLaunchUrl")}
                            help=${msg(
                                "If left empty, authentik will try to extract the launch URL based on the selected provider.",
                            )}
                            input-hint="code"
                        ></ak-text-input>
                        <ak-switch-input
                            name="openInNewTab"
                            ?checked=${app.openInNewTab ?? false}
                            label=${msg("Open in new tab")}
                            help=${msg(
                                "If checked, the launch URL will open in a new browser tab or window from the user's application library.",
                            )}
                        >
                        </ak-switch-input>
                    </div>
                </ak-form-group>
            </form>`;
    }

    renderMain() {
        if (!(this.wizard.app && this.wizard.errors)) {
            throw new Error("Application Step received uninitialized wizard context.");
        }
        return this.renderForm(
            this.wizard.app as ApplicationRequest,
            this.wizard.errors?.app ?? {},
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-application-step": ApplicationWizardApplicationStep;
    }
}
