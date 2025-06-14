import { type NavigableButton, type WizardButton } from "@goauthentik/components/ak-wizard/types";

import { msg } from "@lit/localize";
import { PropertyValues, nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";
import { html, unsafeStatic } from "lit/static-html.js";

import { ApplicationWizardStep } from "../ApplicationWizardStep.js";
import { OneOfProvider } from "../types.js";
import { ApplicationWizardProviderForm } from "./providers/ApplicationWizardProviderForm.js";
import "./providers/ak-application-wizard-provider-for-ldap.js";
import "./providers/ak-application-wizard-provider-for-oauth.js";
import "./providers/ak-application-wizard-provider-for-proxy.js";
import "./providers/ak-application-wizard-provider-for-rac.js";
import "./providers/ak-application-wizard-provider-for-radius.js";
import "./providers/ak-application-wizard-provider-for-saml.js";
import "./providers/ak-application-wizard-provider-for-scim.js";

const providerToTag = new Map([
    ["ldapprovider", "ak-application-wizard-provider-for-ldap"],
    ["oauth2provider", "ak-application-wizard-provider-for-oauth"],
    ["proxyprovider", "ak-application-wizard-provider-for-proxy"],
    ["racprovider", "ak-application-wizard-provider-for-rac"],
    ["radiusprovider", "ak-application-wizard-provider-for-radius"],
    ["samlprovider", "ak-application-wizard-provider-for-saml"],
    ["scimprovider", "ak-application-wizard-provider-for-scim"],
]);

@customElement("ak-application-wizard-provider-step")
export class ApplicationWizardProviderStep extends ApplicationWizardStep {
    @state()
    label = msg("Configure Provider");

    @query("#providerform")
    element!: ApplicationWizardProviderForm<OneOfProvider>;

    get valid() {
        return this.element.valid;
    }

    get formValues() {
        return this.element.formValues;
    }

    override handleButton(button: NavigableButton) {
        if (button.kind === "next") {
            if (!this.valid) {
                this.handleEnabling({
                    disabled: ["bindings", "submit"],
                });
                return;
            }
            const payload = {
                provider: {
                    ...this.formValues,
                    mode: this.wizard.proxyMode,
                },
                errors: this.removeErrors("provider"),
            };
            this.handleUpdate(payload, button.destination, {
                enable: ["bindings", "submit"],
            });
            return;
        }
        super.handleButton(button);
    }

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "bindings" },
            { kind: "back", destination: "provider-choice" },
            { kind: "cancel" },
        ];
    }

    renderMain() {
        if (!this.wizard.providerModel) {
            throw new Error("Attempted to access provider page without providing a provider type.");
        }

        // This is, I'm afraid, some rather esoteric bit of Lit-ing, and it makes ESLint
        // sad.  It does allow us to get away with specifying very little about the
        // provider here.
        const tag = providerToTag.get(this.wizard.providerModel);
        return tag
            ? // eslint-disable-next-line lit/binding-positions,lit/no-invalid-html
              html`<${unsafeStatic(tag)}
                id="providerform"
            .wizard=${this.wizard}
            .errors=${this.wizard.errors?.provider ?? {}}

            ></${
                /* eslint-disable-next-line lit/binding-positions,lit/no-invalid-html */
                unsafeStatic(tag)
            }>`
            : nothing;
    }

    updated(changed: PropertyValues<this>) {
        if (changed.has("wizard")) {
            const label = this.element?.label ?? this.label;
            if (label !== this.label) {
                this.label = label;
            }
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-step": ApplicationWizardProviderStep;
    }
}
