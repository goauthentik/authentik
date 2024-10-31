import "@goauthentik/admin/applications/wizard/ak-wizard-title.js";
import {
    ProxyModeValue,
    type SetMode,
    type SetShowHttpBasic,
    renderForm,
} from "@goauthentik/admin/providers/proxy/ProxyProviderFormForm.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { ProxyMode, ProxyProvider, ValidationError } from "@goauthentik/api";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm";

@customElement("ak-application-wizard-provider-for-proxy")
export class ApplicationWizardProxyProviderForm extends ApplicationWizardProviderForm<ProxyProvider> {
    @state()
    showHttpBasic = true;

    renderForm(provider: ProxyProvider, errors: ValidationError) {
        const onSetMode: SetMode = (ev: CustomEvent<ProxyModeValue>) => {
            this.handleUpdate({ ...this.wizard, proxyMode: ev.detail.value });
            // We deliberately chose not to make the forms "controlled," but we do need this form to
            // respond immediately to a state change in the wizard.
            window.setTimeout(() => this.requestUpdate(), 0);
        };

        const onSetShowHttpBasic: SetShowHttpBasic = (ev: Event) => {
            const el = ev.target as HTMLInputElement;
            this.showHttpBasic = el.checked;
        };

        return html` <ak-wizard-title>${msg("Configure Proxy Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm(provider ?? {}, errors ?? [], {
                    mode: this.wizard.proxyMode ?? ProxyMode.Proxy,
                    onSetMode,
                    showHttpBasic: this.showHttpBasic,
                    onSetShowHttpBasic,
                })}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("Proxy Provider Step received uninitialized wizard context.");
        }
        return this.renderForm(this.wizard.provider as ProxyProvider);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-proxy": ApplicationWizardProxyProviderForm;
    }
}
