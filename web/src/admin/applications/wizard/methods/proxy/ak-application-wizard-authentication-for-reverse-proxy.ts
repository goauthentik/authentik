import {
    ProxyModeValue,
    renderForm,
} from "@goauthentik/admin/providers/proxy/ProxyProviderFormForm.js";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

import BaseProviderPanel from "../BaseProviderPanel.js";

@customElement("ak-application-wizard-authentication-for-reverse-proxy")
export class AkReverseProxyApplicationWizardPage extends BaseProviderPanel {
    @state()
    showHttpBasic = true;

    render() {
        const onSetMode: SetMode = (ev: CustomEvent<ProxyModeValue>) => {
            this.dispatchWizardUpdate({
                update: {
                    ...this.wizard,
                    proxyMode: ev.detail.value,
                },
            });
            // We deliberately chose not to make the forms "controlled," but we do need this form to
            // respond immediately to a state change in the wizard.
            window.setTimeout(() => this.requestUpdate(), 0);
        };

        const onSetShowHttpBasic: SetShowHttpBasic = (ev: Event) => {
            const el = ev.target as HTMLInputElement;
            this.showHttpBasic = el.checked;
        };

        return html` <ak-wizard-title>${msg("Configure Proxy Provider")}</ak-wizard-title>
            <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
                ${renderForm(this.wizard.provider ?? {}, this.wizard.errors.provider ?? [], {
                    mode: this.wizard.proxyMode,
                    onSetMode,
                    showHttpBasic: this.showHttpBasic,
                    onSetShowHttpBasic,
                })}
            </form>`;
    }
}

export default AkReverseProxyApplicationWizardPage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-authentication-for-reverse-proxy": AkReverseProxyApplicationWizardPage;
    }
}
