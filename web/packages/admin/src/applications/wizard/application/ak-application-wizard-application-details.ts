import { policyOptions } from "@goauthentik/admin/applications/ApplicationForm";
import { first } from "@goauthentik/common/utils.js";
import "@goauthentik/components/ak-radio-input.js";
import "@goauthentik/components/ak-slug-input.js";
import "@goauthentik/components/ak-switch-input.js";
import "@goauthentik/components/ak-text-input.js";
import "@goauthentik/elements/forms/FormGroup.js";
import "@goauthentik/elements/forms/HorizontalFormElement.js";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import BasePanel from "../BasePanel";

@customElement("ak-application-wizard-application-details")
export class ApplicationWizardApplicationDetails extends BasePanel {
    handleChange(_ev: Event) {
        const formValues = this.formValues;
        if (!formValues) {
            throw new Error("No application values on form?");
        }
        this.dispatchWizardUpdate({
            update: {
                ...this.wizard,
                app: formValues,
            },
            status: this.valid ? "valid" : "invalid",
        });
    }

    render(): TemplateResult {
        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${ifDefined(this.wizard.app?.name)}
                label=${msg("Name")}
                required
                help=${msg("Application's display Name.")}
                id="ak-application-wizard-details-name"
                .errorMessages=${this.wizard.errors.app?.name ?? []}
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                value=${ifDefined(this.wizard.app?.slug)}
                label=${msg("Slug")}
                source="#ak-application-wizard-details-name"
                required
                help=${msg("Internal application name used in URLs.")}
                .errorMessages=${this.wizard.errors.app?.slug ?? []}
            ></ak-slug-input>
            <ak-text-input
                name="group"
                value=${ifDefined(this.wizard.app?.group)}
                label=${msg("Group")}
                .errorMessages=${this.wizard.errors.app?.group ?? []}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                )}
            ></ak-text-input>
            <ak-radio-input
                label=${msg("Policy engine mode")}
                required
                name="policyEngineMode"
                .options=${policyOptions}
                .value=${this.wizard.app?.policyEngineMode}
                .errorMessages=${this.wizard.errors.app?.policyEngineMode ?? []}
            ></ak-radio-input>
            <ak-form-group aria-label="UI Settings">
                <span slot="header"> ${msg("UI Settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="metaLaunchUrl"
                        label=${msg("Launch URL")}
                        value=${ifDefined(this.wizard.app?.metaLaunchUrl)}
                        help=${msg(
                            "If left empty, authentik will try to extract the launch URL based on the selected provider.",
                        )}
                        .errorMessages=${this.wizard.errors.app?.metaLaunchUrl ?? []}
                    ></ak-text-input>
                    <ak-switch-input
                        name="openInNewTab"
                        ?checked=${first(this.wizard.app?.openInNewTab, false)}
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
}

export default ApplicationWizardApplicationDetails;
