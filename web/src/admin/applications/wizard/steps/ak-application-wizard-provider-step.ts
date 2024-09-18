import { type WizardButton } from "@goauthentik/components/ak-wizard/types";

import { msg } from "@lit/localize";
import { nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";
import { html, unsafeStatic } from "lit/static-html.js";

import { ApplicationWizardStep } from "../ApplicationWizardStep.js";
import "./providers/ak-application-wizard-provider-for-forward-domain-proxy.js";
import "./providers/ak-application-wizard-provider-for-ldap.js";
import "./providers/ak-application-wizard-provider-for-oauth.js";
import "./providers/ak-application-wizard-provider-for-rac.js";
import "./providers/ak-application-wizard-provider-for-radius.js";
import "./providers/ak-application-wizard-provider-for-reverse-proxy.js";
import "./providers/ak-application-wizard-provider-for-saml.js";
import "./providers/ak-application-wizard-provider-for-scim.js";
import "./providers/ak-application-wizard-provider-for-single-forward-proxy.js";

const providerToTag = new Map([
    ["ldapprovider", "ak-application-wizard-provider-for-ldap"],
    ["oauth2provider", "ak-application-wizard-provider-for-oauth"],
    ["proxyprovider-forwarddomain", "ak-application-wizard-provider-for-forward-domain-proxy"],
    ["proxyprovider-forwardsingle", "ak-application-wizard-provider-for-single-forward-proxy"],
    ["proxyprovider-proxy", "ak-application-wizard-provider-for-reverse-proxy"],
    ["racprovider", "ak-application-wizard-provider-for-rac"],
    ["radiusprovider", "ak-application-wizard-provider-for-radius"],
    ["samlprovider", "ak-application-wizard-provider-for-saml"],
    ["scimprovider", "ak-application-wizard-provider-for-scim"],
]);

@customElement("ak-application-wizard-provider-step")
export class ApplicationWizardProviderStep extends ApplicationWizardStep {
    @state()
    label = msg("Configure Provider");

    @state()
    errors = new Map<string, string>();

    @query("#providerform")
    form!: HTMLFormElement;

    override handleNavigationEvent(button: WizardButton) {
        if (button.kind === "next" && !this.form.valid) {
            this.dispatchUpdate({
                status: { disable: ["bindings", "submit"] },
            });
            return;
        }

        this.dispatchUpdate({
            update: { provider: this.formValues },
            status: { enable: "bindings" },
        });
        super.handleNavigationEvent(button);
    }

    get buttons(): WizardButton[] {
        return [
            { kind: "next", destination: "submit" },
            { kind: "back", destination: "provider-choice" },
            { kind: "cancel" },
        ];
    }

    renderMain() {
        const tag = providerToTag.get(this.wizard.providerModel);
        return tag
            ? html`<${unsafeStatic(tag)}
                id="providerform"
            .wizard=${this.wizard}
            .errors=${this.errors}
            ></${unsafeStatic(tag)}>`
            : nothing;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-step": ApplicationWizardProviderStep;
    }
}
