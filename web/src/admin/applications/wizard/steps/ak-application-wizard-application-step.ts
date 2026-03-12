import "#admin/applications/wizard/ak-wizard-title";
import "#components/ak-file-search-input";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { omitKeys, trimMany } from "#common/objects";

import { isSlug } from "#elements/router/utils";

import { type NavigableButton, type WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import {
    ApplicationWizardStateUpdate,
    WizardValidationRecord,
} from "#admin/applications/wizard/steps/providers/shared";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { AdminFileListUsageEnum, type ApplicationRequest } from "@goauthentik/api";

import { snakeCase } from "change-case";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * The first step of the application wizard, responsible for collecting
 * basic application information such as name, slug, group, and UI settings.
 *
 * This step performs validation on the form inputs and updates the wizard state accordingly when the "Next" button is clicked.
 *
 * @prop wizard - The current state of the application wizard, shared across all steps.
 */
@customElement("ak-application-wizard-application-step")
export class ApplicationWizardApplicationStep extends ApplicationWizardStep {
    label = msg("Application");

    @state()
    errors = new Map<keyof ApplicationRequest, string>();

    public get form(): HTMLFormElement | null {
        return this.renderRoot.querySelector("form#applicationform");
    }

    constructor() {
        super();
        // This is the first step. Ensure it is always enabled.
        this.enabled = true;
    }

    protected errorMessages(name: keyof ApplicationRequest) {
        return this.errors.has(name)
            ? [this.errors.get(name)]
            : (this.wizard.errors?.app?.[name] ?? this.wizard.errors?.app?.[snakeCase(name)] ?? []);
    }

    get buttons(): WizardButton[] {
        return [{ kind: "next", destination: "provider-choice" }, { kind: "cancel" }];
    }

    get valid() {
        this.errors = new Map();

        const values = trimMany(this.formValues, "metaLaunchUrl", "name", "slug");

        if (!values.name) {
            this.errors.set("name", msg("An application name is required"));
        }

        if (values.metaLaunchUrl && !URL.canParse(values.metaLaunchUrl)) {
            this.errors.set("metaLaunchUrl", msg("Not a valid URL"));
        }

        if (!values.slug || !isSlug(values.slug)) {
            this.errors.set("slug", msg("Not a valid slug"));
        }

        return this.errors.size === 0;
    }

    public override handleButton(button: NavigableButton) {
        if (button.kind !== "next") {
            return super.handleButton(button);
        }

        if (!this.valid) {
            this.handleEnabling({
                disabled: ["provider-choice", "provider", "bindings", "submit"],
            });

            return;
        }

        const app = { ...this.formValues };

        const payload: ApplicationWizardStateUpdate = {
            app,
            errors: omitKeys(this.wizard.errors, "app"),
        };

        if (!this.wizard.provider?.name?.trim() && app.name) {
            payload.provider = {
                name: `Provider for ${app.name}`,
            };
        }

        this.handleUpdate(payload, button.destination, {
            enable: "provider-choice",
        });
    }

    protected renderForm(app: Partial<ApplicationRequest>, errors: WizardValidationRecord = {}) {
        return html` <ak-wizard-title>${msg("Configure the Application")}</ak-wizard-title>
            <form id="applicationform" class="pf-c-form pf-m-horizontal" slot="form">
                <ak-text-input
                    name="name"
                    autocomplete="off"
                    placeholder=${msg("Type an application name...")}
                    value=${ifDefined(app.name)}
                    label=${msg("Application Name")}
                    spellcheck="false"
                    required
                    .errorMessages=${errors.name ?? this.errorMessages("name")}
                    help=${msg("The name displayed in the application library.")}
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
                    placeholder=${msg("e.g. my-application")}
                ></ak-slug-input>
                <ak-text-input
                    name="group"
                    value=${ifDefined(app.group)}
                    label=${msg("Group")}
                    placeholder=${msg("e.g. Collaboration, Communication, Internal, etc.")}
                    .errorMessages=${errors.group}
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
                    .errorMessages=${errors.policyEngineMode}
                ></ak-radio-input>
                <ak-form-group label=${msg("UI Settings")}>
                    <div class="pf-c-form">
                        <ak-text-input
                            name="metaLaunchUrl"
                            label=${msg("Launch URL")}
                            placeholder=${msg("https://...")}
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
                        <ak-file-search-input
                            name="metaIcon"
                            label=${msg("Icon")}
                            value=${ifDefined(app.metaIcon)}
                            .usage=${AdminFileListUsageEnum.Media}
                            help=${msg(
                                "Select from uploaded files, or type a Font Awesome icon (fa://fa-icon-name) or URL.",
                            )}
                            blankable
                        ></ak-file-search-input>
                        <ak-text-input
                            label=${msg("Publisher")}
                            name="metaPublisher"
                            value="${ifDefined(app.metaPublisher)}"
                            .errorMessages=${errors.metaPublisher}
                            help=${msg("The publisher is shown in the application library.")}
                        ></ak-text-input>
                        <ak-textarea-input
                            label=${msg("Description")}
                            name="metaDescription"
                            value=${ifDefined(app.metaDescription)}
                            .errorMessages=${errors.metaDescription}
                            help=${msg(
                                "The description is shown in the application library and may provide additional information about the application to end users.",
                            )}
                        ></ak-textarea-input>
                    </div>
                </ak-form-group>
            </form>`;
    }

    renderMain() {
        if (!(this.wizard.app && this.wizard.errors)) {
            throw new Error("Application Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.app, this.wizard.errors?.app);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-application-step": ApplicationWizardApplicationStep;
    }
}
