import { AKElement } from "#elements/Base";
import { DEFAULT_CONFIG } from "#common/api/config";
import { AuthenticatorsApi, Device } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

interface StaticToken {
    token: string;
}

export function downloadCodes(codes: string[] | { token: string }[]): void {
    if (!codes || codes.length === 0) return;
    
    const content = codes.map(code => typeof code === "string" ? code : code.token).join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = 'authentik-recovery-codes.txt';
    document.body.appendChild(a);
    a.click();
    
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
}

export function printCodes(codes: string[] | { token: string }[]): void {
    if (!codes || codes.length === 0) return;
    
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    
    const codeItems = codes.map(code => {
        const codeText = typeof code === "string" ? code : code.token;
        return `<div class="code">${codeText}</div>`;
    }).join('');
    
    const htmlContent = `
        <html>
            <head>
                <title>authentik - Recovery Codes</title>
                <style>
                    body {
                        font-family: monospace;
                        padding: 20px;
                    }
                    h1 {
                        font-size: 18px;
                        margin-bottom: 20px;
                    }
                    .codes {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 10px;
                    }
                    .code {
                        font-size: 16px;
                        padding: 5px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        text-align: center;
                    }
                    .instructions {
                        margin-top: 20px;
                        font-size: 12px;
                    }
                </style>
            </head>
            <body>
                <h1>authentik - Recovery Codes</h1>
                <div class="codes">
                    ${codeItems}
                </div>
                <div class="instructions">
                    <p>${msg("Keep these recovery codes in a safe place. Each code can only be used once.")}</p>
                    <p>${msg("If you lose access to your authenticator device, you can use one of these codes to sign in.")}</p>
                </div>
            </body>
        </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);
}

@customElement("ak-user-settings-authenticator-static-modal")
export class UserSettingsAuthenticatorStaticModal extends AKElement {
    @property({ attribute: false })
    device?: Device;

    @state()
    tokens: StaticToken[] = [];

    @state()
    loading = true;

    @state()
    error = "";

    static styles: CSSResult[] = [
        PFBase,
        PFCard,
        PFButton,
        PFContent,
        PFDisplay,
        PFFlex,
        PFList,
        PFTitle,
    ];

    async firstUpdated(): Promise<void> {
        await this.loadData();
    }

    async loadData(): Promise<void> {
        if (!this.device) return;
        
        this.loading = true;
        this.error = "";
        
        try {
            const api = new AuthenticatorsApi(DEFAULT_CONFIG);
            const response = await api.authenticatorsStaticRetrieve({
                id: parseInt(this.device.pk, 10),
            });
            
            if (response && response.tokenSet) {
                this.tokens = response.tokenSet;
            } else {
                this.tokens = [];
            }
        } catch (e) {
            console.error("Failed to load recovery codes", e);
            this.error = msg("Failed to load recovery codes. Please try again.");
        } finally {
            this.loading = false;
        }
    }

    downloadCodes(): void {
        downloadCodes(this.tokens);
    }

    printCodes(): void {
        printCodes(this.tokens);
    }

    render(): TemplateResult {
        if (this.loading) {
            return html`<div class="pf-c-content">
                <p>${msg("Loading recovery codes...")}</p>
            </div>`;
        }
        
        if (this.error) {
            return html`<div class="pf-c-content">
                <p class="pf-m-danger">${this.error}</p>
            </div>`;
        }
        
        if (!this.tokens || this.tokens.length === 0) {
            return html`<div class="pf-c-content">
                <p>${msg("No recovery codes found for this device.")}</p>
            </div>`;
        }
        
        return html`
            <div class="pf-c-content">
                <p>
                    ${msg("These recovery codes can be used to sign in when you don't have access to your other authentication methods. Each code can only be used once.")}
                </p>
                
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-l-grid__item pf-m-12-col">
                        <ul class="pf-c-list pf-m-plain pf-u-text-align-center" style="columns: 2; column-gap: 2rem;">
                            ${this.tokens.map(token => html`
                                <li class="pf-u-py-sm">
                                    <code class="pf-u-font-size-lg">${token.token}</code>
                                </li>
                            `)}
                        </ul>
                    </div>
                </div>
                
                <div class="pf-l-flex pf-m-justify-content-center pf-m-align-items-center pf-m-gap-md pf-u-mt-xl pf-u-mb-md">
                    <button
                        class="pf-c-button pf-m-primary pf-m-block"
                        style="max-width: 200px;"
                        @click=${this.downloadCodes}
                    >
                        <i class="fas fa-download pf-u-mr-xs" aria-hidden="true"></i>
                        ${msg("Download")}
                    </button>
                    <button
                        class="pf-c-button pf-m-secondary pf-m-block"
                        style="max-width: 200px;"
                        @click=${this.printCodes}
                    >
                        <i class="fas fa-print pf-u-mr-xs" aria-hidden="true"></i>
                        ${msg("Print")}
                    </button>
                </div>
                
                <p class="pf-u-text-align-center pf-u-mt-md pf-u-font-size-sm">
                    ${msg("Keep these codes in a safe place. If you lose your authenticator device, these codes are your backup method to access your account.")}
                </p>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-settings-authenticator-static-modal": UserSettingsAuthenticatorStaticModal;
    }
} 