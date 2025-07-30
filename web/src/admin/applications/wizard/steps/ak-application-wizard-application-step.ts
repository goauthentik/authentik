import "#admin/applications/wizard/ak-wizard-title";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { ApplicationWizardStateUpdate, ValidationRecord } from "../types.js";

import { isSlug } from "#elements/router/utils";

import { type NavigableButton, type WizardButton } from "#components/ak-wizard/types";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { type ApplicationRequest } from "@goauthentik/api";

import { snakeCase } from "change-case";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, query, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

function trimMany<T extends object, K extends keyof T>(target: T, keys: K[]): Pick<T, K> {
    const output = {} as Record<K, unknown>;

    for (const key of keys) {
        const value = target[key];

        output[key] = typeof value === "string" ? value.trim() : value;
    }

    return output as Pick<T, K>;
}

@customElement("ak-application-wizard-application-step")
export class ApplicationWizardApplicationStep extends ApplicationWizardStep {
    label = msg("Application");

    @state()
    errors = new Map<keyof ApplicationRequest, string>();

    @query("form#applicationform")
    form!: HTMLFormElement;

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

        const values = trimMany(this.formValues, ["metaLaunchUrl", "name", "slug"]);

        if (!values.name) {
            this.errors.set("name", msg("An application name is required"));
        }

        if (!values.metaLaunchUrl || !URL.canParse(values.metaLaunchUrl)) {
            this.errors.set("metaLaunchUrl", msg("Not a valid URL"));
        }

        if (!values.slug || !isSlug(values.slug)) {
            this.errors.set("slug", msg("Not a valid slug"));
        }

        return this.errors.size === 0;
    }

    override handleButton(button: NavigableButton) {
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
            errors: this.removeErrors("app"),
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
                <ak-form-group label=${msg("UI Settings")}>
                    <div class="pf-c-form">
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
