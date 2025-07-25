import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { FlowChallengeResponseRequest, SAMLIframeLogoutChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

interface LogoutStatus {
    providerName: string;
    status: "pending" | "success" | "error";
}

interface LogoutURLData {
    url: string;
    saml_request?: string;
    provider_name?: string;
    binding?: string;
}

@customElement("ak-stage-saml-iframe-logout")
export class SAMLIframeLogoutStage extends BaseStage<
    SAMLIframeLogoutChallenge,
    FlowChallengeResponseRequest
> {
    @state()
    logoutStatuses: LogoutStatus[] = [];

    @state()
    completedCount = 0;

    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFButton,
        PFFormControl,
        PFTitle,
        PFProgress,
        css`
            .ak-hidden {
                display: none;
            }
            .provider-status {
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .status-icon {
                width: 1.5rem;
                height: 1.5rem;
            }
            .status-pending {
                color: var(--pf-c-spinner--Color);
            }
            .status-success {
                color: var(--pf-global--success-color--100);
            }
            .status-error {
                color: var(--pf-global--danger-color--100);
            }
            .pf-c-spinner {
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }
        `,
    ];

    firstUpdated(changedProperties: PropertyValues): void {
        super.firstUpdated(changedProperties);


        // If no logout URLs, immediately submit
        if (!this.challenge.logoutUrls || this.challenge.logoutUrls.length === 0) {
            const submitEvent = new Event("submit") as SubmitEvent;
            this.submitForm(submitEvent);
            return;
        }

        // Initialize status tracking
        this.logoutStatuses = this.challenge.logoutUrls.map((url: LogoutURLData) => ({
            providerName: url.provider_name || "Unknown Provider",
            status: "pending",
        }));

        // Start the logout process
        this.performLogouts();
    }

    async performLogouts(): Promise<void> {
        const timeout = this.challenge.timeout || 5000;

        // Create iframes for each logout URL
        this.challenge.logoutUrls?.forEach((logoutData: LogoutURLData, index: number) => {
            this.createLogoutIframe(logoutData, index, timeout);
        });

        // Set a final timeout to complete even if some iframes don't respond
        setTimeout(() => {
            if (this.completedCount < (this.challenge.logoutUrls?.length || 0)) {
                const submitEvent = new Event("submit") as SubmitEvent;
            this.submitForm(submitEvent);
            }
        }, timeout + 1000);
    }

    createLogoutIframe(logoutData: LogoutURLData, index: number, timeout: number): void {
        
        const iframe = document.createElement("iframe");
        iframe.style.display = "none";
        iframe.name = `saml-logout-${index}`;

        // Add to document
        document.body.appendChild(iframe);

        // Set up timeout
        const timeoutId = setTimeout(() => {
            this.handleLogoutComplete(index, false);
            iframe.remove();
        }, timeout);

        // Try to detect when iframe loads (may not work for cross-origin)
        iframe.addEventListener("load", () => {
            clearTimeout(timeoutId);
            this.handleLogoutComplete(index, true);
            setTimeout(() => {
                iframe.remove();
            }, 100);
        });

        // Handle based on binding type
        if (logoutData.binding === "REDIRECT" || !logoutData.saml_request) {
            // For REDIRECT binding, just navigate the iframe to the URL
            iframe.src = logoutData.url;
        } else {
            // For POST binding, create and submit a form
            const form = document.createElement("form");
            form.method = "POST";
            form.action = logoutData.url;
            form.target = iframe.name;

            // Add SAML request
            const samlInput = document.createElement("input");
            samlInput.type = "hidden";
            samlInput.name = "SAMLRequest";
            samlInput.value = logoutData.saml_request;
            form.appendChild(samlInput);

            // Add to document and submit
            document.body.appendChild(form);
            form.submit();
            
            // Clean up form after submission
            setTimeout(() => {
                form.remove();
            }, 100);
        }
    }

    handleLogoutComplete(index: number, success: boolean): void {
        // Update status
        const statuses = [...this.logoutStatuses];
        statuses[index] = {
            ...statuses[index],
            status: success ? "success" : "error",
        };
        this.logoutStatuses = statuses;

        // Increment completed count
        this.completedCount++;

        // Check if all are done
        if (this.completedCount >= (this.challenge.logoutUrls?.length || 0)) {
            // All done, submit the form
            setTimeout(() => {
                const submitEvent = new Event("submit") as SubmitEvent;
            this.submitForm(submitEvent);
            }, 500);
        }
    }

    renderStatusIcon(status: string): TemplateResult {
        switch (status) {
            case "pending":
                return html`<i class="fas fa-spinner pf-c-spinner status-icon status-pending"></i>`;
            case "success":
                return html`<i class="fas fa-check-circle status-icon status-success"></i>`;
            case "error":
                return html`<i class="fas fa-times-circle status-icon status-error"></i>`;
            default:
                return html``;
        }
    }

    renderProgress(): TemplateResult {
        const total = this.challenge.logoutUrls?.length || 0;
        const percentage = total > 0 ? Math.round((this.completedCount / total) * 100) : 0;

        return html`
            <div class="pf-c-progress">
                <div class="pf-c-progress__description">
                    ${msg("Logging out of SAML providers...")}
                </div>
                <div class="pf-c-progress__status">
                    <span class="pf-c-progress__measure">${this.completedCount} / ${total}</span>
                </div>
                <div
                    class="pf-c-progress__bar"
                    role="progressbar"
                    aria-valuemin="0"
                    aria-valuemax="100"
                    aria-valuenow="${percentage}"
                >
                    <div class="pf-c-progress__indicator" style="width: ${percentage}%;"></div>
                </div>
            </div>
        `;
    }

    render(): TemplateResult {
        // If no logout URLs, show loading (will auto-submit)
        if (!this.challenge.logoutUrls || this.challenge.logoutUrls.length === 0) {
            return html`<ak-flow-card .challenge=${this.challenge} loading></ak-flow-card>`;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("SAML Single Logout")}</span>
            <form class="pf-c-form">
                <div class="pf-c-form__group">${this.renderProgress()}</div>
                <div class="pf-c-form__group">
                    ${this.logoutStatuses.map(
                        (status) => html`
                            <div class="provider-status">
                                ${this.renderStatusIcon(status.status)}
                                <span>${status.providerName}</span>
                            </div>
                        `,
                    )}
                </div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-saml-iframe-logout": SAMLIframeLogoutStage;
    }
}
