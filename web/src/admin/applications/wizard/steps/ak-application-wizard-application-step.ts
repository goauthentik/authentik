import { ApplicationWizardStep } from "@goauthentik/admin/applications/wizard/ApplicationWizardStep.js";
import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import { policyEngineModes } from "@goauthentik/admin/policies/PolicyEngineModes";
import { isSlug } from "@goauthentik/common/utils.js";
import { camelToSnake } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-slug-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import { type NavigableButton, type WizardButton } from "@goauthentik/components/ak-wizard/types";
import { type KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, query, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { type ApplicationRequest } from "@goauthentik/api";

import { ApplicationWizardStateUpdate, ValidationRecord } from "../types";

const autoTrim = (v: unknown) => (typeof v === "string" ? v.trim() : v);

const trimMany = (o: KeyUnknown, vs: string[]) =>
    Object.fromEntries(vs.map((v) => [v, autoTrim(o[v])]));

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const isStr = (v: any): v is string => typeof v === "string";

@customElement("ak-application-wizard-application-step")
export class ApplicationWizardApplicationStep extends ApplicationWizardStep {
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

    get valid() {
        this.errors = new Map();
        const values = trimMany(this.formValues ?? {}, ["metaLaunchUrl", "name", "slug"]);

        if (values["name"] === "") {
            this.errors.set("name", msg("An application name is required"));
        }
        if (
            !(
                isStr(values["metaLaunchUrl"]) &&
                (values["metaLaunchUrl"] === "" || URL.canParse(values["metaLaunchUrl"]))
            )
        ) {
            this.errors.set("metaLaunchUrl", msg("Not a valid URL"));
        }
        if (!(isStr(values["slug"]) && values["slug"] !== "" && isSlug(values["slug"]))) {
            this.errors.set("slug", msg("Not a valid slug"));
        }
        return this.errors.size === 0;
    }

    override handleButton(button: NavigableButton) {
        if (button.kind === "next") {
            if (!this.valid) {
                this.handleEnabling({
                    disabled: ["provider-choice", "provider", "bindings", "submit"],
                });
                return;
            }
            const app: Partial<ApplicationRequest> = this.formValues as Partial<ApplicationRequest>;

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
            return;
        }
        super.handleButton(button);
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
                    id="ak-application-wizard-details-name"
                ></ak-text-input>
                <ak-slug-input
                    name="slug"
                    value=${ifDefined(app.slug)}
                    label=${msg("Slug")}
                    source="#ak-application-wizard-details-name"
                    required
                    ?invalid=${errors.slug ?? this.errors.has("slug")}
                    .errorMessages=${this.errorMessages("slug")}
                    help=${msg("Internal application name used in URLs.")}
                ></ak-slug-input>
                <ak-text-input
                    name="group"
                    value=${ifDefined(app.group)}
                    label=${msg("Group")}
                    .errorMessages=${errors.group ?? []}
                    help=${msg(
                        "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                    )}
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
