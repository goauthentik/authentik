import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-ldap";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-oauth";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-proxy";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-rac";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-radius";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-saml";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-saml-metadata";
import "#admin/applications/wizard/steps/providers/ak-application-wizard-provider-for-scim";

import { omitKeys } from "#common/objects";

import { StrictUnsafe } from "#elements/utils/unsafe";

import { type NavigableButton, type WizardButton } from "#components/ak-wizard/shared";

import { ApplicationWizardStep } from "#admin/applications/wizard/ApplicationWizardStep";
import { ApplicationWizardProviderForm } from "#admin/applications/wizard/steps/providers/ApplicationWizardProviderForm";
import { OneOfProvider } from "#admin/applications/wizard/steps/providers/shared";

import { msg } from "@lit/localize";
import { nothing, PropertyValues } from "lit";
import { customElement, query, state } from "lit/decorators.js";

const providerToTag = {
    ldapprovider: "ak-application-wizard-provider-for-ldap",
    oauth2provider: "ak-application-wizard-provider-for-oauth",
    proxyprovider: "ak-application-wizard-provider-for-proxy",
    racprovider: "ak-application-wizard-provider-for-rac",
    radiusprovider: "ak-application-wizard-provider-for-radius",
    samlprovider: "ak-application-wizard-provider-for-saml",
    samlproviderimportmodel: "ak-application-wizard-provider-for-saml-metadata",
    scimprovider: "ak-application-wizard-provider-for-scim",
} as const satisfies Record<string, string>;

type ProviderModel = keyof typeof providerToTag;

/**
 * @prop wizard - The current state of the application wizard, shared across all steps.
 */
@customElement("ak-application-wizard-provider-step")
export class ApplicationWizardProviderStep extends ApplicationWizardStep {
    @state()
    public override label = msg("Configure Provider");

    @query("#providerform")
    protected element!: ApplicationWizardProviderForm<OneOfProvider>;

    get form(): HTMLFormElement | null {
        const providerForm = this.element.form;

        if (!providerForm) {
            // TODO: This needs to be removed once all steps can report their validity.
            console.debug(
                "authentik/wizard: Form not found within provider step",
                this,
                this.element,
            );

            return null;
        }

        return providerForm;
    }

    get valid() {
        return this.element.valid;
    }

    get formValues() {
        return this.element.formValues;
    }

    public override handleButton(button: NavigableButton) {
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
                errors: omitKeys(this.wizard.errors, "provider"),
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
            { kind: "cancel" },
            { kind: "back", destination: "provider-choice" },
            { kind: "next", destination: "bindings" },
        ];
    }

    renderMain() {
        if (!this.wizard.providerModel) {
            throw new Error("Attempted to access provider page without providing a provider type.");
        }

        // This is, I'm afraid, some rather esoteric bit of Lit-ing, and it makes ESLint
        // sad.  It does allow us to get away with specifying very little about the
        // provider here.
        const tag = providerToTag[this.wizard.providerModel as ProviderModel];

        if (!tag) {
            this.logger.warn(
                `No provider form found for provider model ${this.wizard.providerModel}`,
            );

            return nothing;
        }

        return StrictUnsafe<ApplicationWizardProviderForm<OneOfProvider>>(tag, {
            wizard: this.wizard,
            id: "providerform",
            errors: this.wizard.errors?.provider ?? {},
        });
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
