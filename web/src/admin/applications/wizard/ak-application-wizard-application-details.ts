import { policyOptions } from "@goauthentik/admin/applications/ApplicationForm";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

import ApplicationWizardPageBase from "./ApplicationWizardPageBase";

@customElement("ak-application-wizard-application-details")
export class ApplicationWizardApplicationDetails extends ApplicationWizardPageBase {
    handleChange(ev: Event) {
        const value = ev.target.type === "checkbox" ? ev.target.checked : ev.target.value;
        this.dispatchWizardUpdate({
            application: {
                ...this.wizard.application,
                [ev.target.name]: value,
            },
        });
    }

    render(): TemplateResult {
        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${this.wizard.application?.name}
                label=${msg("Name")}
                required
                help=${msg("Application's display Name.")}
            ></ak-text-input>
            <ak-text-input
                name="slug"
                value=${this.wizard.application?.slug}
                label=${msg("Slug")}
                required
                help=${msg("Internal application name used in URLs.")}
            ></ak-text-input>
            <ak-text-input
                name="group"
                value=${this.wizard.application?.group}
                label=${msg("Group")}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together."
                )}
            ></ak-text-input>
            <ak-radio-input
                label=${msg("Policy engine mode")}
                required
                name="policyEngineMode"
                .options=${policyOptions}
                .value=${this.wizard.application?.policyEngineMode}
            ></ak-radio-input>
            <ak-form-group>
                <span slot="header"> ${msg("UI settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="metaLaunchUrl"
                        label=${msg("Launch URL")}
                        value=${ifDefined(this.wizard.application?.metaLaunchUrl)}
                        help=${msg(
                            "If left empty, authentik will try to extract the launch URL based on the selected provider."
                        )}
                    ></ak-text-input>
                    <ak-switch-input
                        name="openInNewTab"
                        ?checked=${first(this.wizard.application?.openInNewTab, false)}
                        label=${msg("Open in new tab")}
                        help=${msg(
                            "If checked, the launch URL will open in a new browser tab or window from the user's application library."
                        )}
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>
        </form>`;
    }
}

export default ApplicationWizardApplicationDetails;
