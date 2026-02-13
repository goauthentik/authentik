import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import {
    FlowChallengeResponseRequest,
    IframeLogoutChallenge,
    LogoutURL,
    SAMLBindingsEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFProgress from "@patternfly/patternfly/components/Progress/progress.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

enum LogoutStatusStatus {
    Pending = "pending",
    Success = "success",
    Error = "error",
}

interface LogoutStatus {
    providerName: string;
    status: LogoutStatusStatus;
}

function renderStatusIcon(status: LogoutStatusStatus): TemplateResult | typeof nothing {
    switch (status) {
        case LogoutStatusStatus.Pending:
            return html`<i class="fas fa-spinner pf-c-spinner status-icon status-pending"></i>`;
        case LogoutStatusStatus.Success:
            return html`<i class="fas fa-check-circle status-icon status-success"></i>`;
        case LogoutStatusStatus.Error:
            return html`<i class="fas fa-times-circle status-icon status-error"></i>`;
    }
}

@customElement("ak-provider-iframe-logout")
export class IFrameLogoutStage extends BaseStage<
    IframeLogoutChallenge,
    FlowChallengeResponseRequest
> {
    @state()
    protected logoutStatuses: LogoutStatus[] = [];

    @state()
    protected completedCount = 0;

    #iframeTimeouts = new Map<number, ReturnType<typeof setTimeout>>();
    #moveOnTimeout?: ReturnType<typeof setTimeout>;

    public override disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#iframeTimeouts.forEach((id) => {
            clearTimeout(id);
        });
        clearTimeout(this.#moveOnTimeout);
    }

    public static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFButton,
        PFFormControl,
        PFTitle,
        PFProgress,
        css`
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

    public override firstUpdated(changedProperties: PropertyValues): void {
        super.firstUpdated(changedProperties);

        // Initialize status tracking
        const logoutUrls = (this.challenge?.logoutUrls as LogoutURL[]) || [];

        this.logoutStatuses = logoutUrls.map(
            (url): LogoutStatus => ({
                providerName: url.providerName || msg("Unknown Provider"),
                status: LogoutStatusStatus.Pending,
            }),
        );

        // Start the logout process
        this.performLogouts();
    }

    protected async performLogouts(): Promise<void> {
        const logoutUrls = (this.challenge?.logoutUrls as LogoutURL[]) || [];

        // Create iframes for each logout URL
        logoutUrls.forEach((logoutData, index) => {
            this.createLogoutIframe(logoutData, index);
        });

        // Set a final timeout to complete even if some iframes don't respond
        this.#moveOnTimeout = setTimeout(() => {
            if (this.completedCount < logoutUrls.length) {
                const submitEvent = new SubmitEvent("submit");
                this.submitForm(submitEvent);
            }
        }, 6000); // 6 seconds (5 second timeout + 1 second buffer)
    }

    protected createLogoutIframe(logoutData: LogoutURL, index: number): void {
        const iframe = document.createElement("iframe");
        iframe.style.display = "none";
        iframe.name = `saml-logout-${index}`;

        // Add to document
        document.body.appendChild(iframe);

        // Set up timeout
        const timeoutId = setTimeout(() => {
            this.handleLogoutComplete(index, false);
            iframe.remove();
        }, 5000); // 5 second timeout
        this.#iframeTimeouts.set(index, timeoutId);

        // Try to detect when iframe loads (may not work for cross-origin)
        iframe.addEventListener("load", () => {
            const timeout = this.#iframeTimeouts.get(index);
            if (timeout) {
                clearTimeout(timeout);
                this.#iframeTimeouts.delete(index);
            }
            this.handleLogoutComplete(index, true);
            iframe.remove();
        });

        // Handle based on binding type
        if (
            logoutData.binding === SAMLBindingsEnum.Redirect ||
            (!logoutData.samlRequest && !logoutData.samlResponse)
        ) {
            // For REDIRECT binding, just navigate the iframe to the URL
            iframe.src = logoutData.url;
        } else {
            // For POST binding, create and submit a form
            const form = document.createElement("form");
            form.method = "POST";
            form.action = logoutData.url;
            form.target = iframe.name;

            // Add SAML request OR response (depending on which is present)
            if (logoutData.samlRequest) {
                const samlInput = document.createElement("input");
                samlInput.type = "hidden";
                samlInput.name = "SAMLRequest";
                samlInput.value = logoutData.samlRequest;
                form.appendChild(samlInput);
            } else if (logoutData.samlResponse) {
                const samlInput = document.createElement("input");
                samlInput.type = "hidden";
                samlInput.name = "SAMLResponse";
                samlInput.value = logoutData.samlResponse;
                form.appendChild(samlInput);
            }

            // Add RelayState if present
            if (logoutData.samlRelayState) {
                const relayInput = document.createElement("input");
                relayInput.type = "hidden";
                relayInput.name = "RelayState";
                relayInput.value = logoutData.samlRelayState;
                form.appendChild(relayInput);
            }

            // Add to document and submit
            document.body.appendChild(form);
            form.submit();

            // Clean up form after submission
            form.remove();
        }
    }

    protected handleLogoutComplete(index: number, success: boolean): void {
        // Update status
        const statuses = [...this.logoutStatuses];
        statuses[index] = {
            ...statuses[index],
            status: success ? LogoutStatusStatus.Success : LogoutStatusStatus.Error,
        };
        this.logoutStatuses = statuses;

        // Increment completed count
        this.completedCount++;

        // Check if all are done
        if (this.completedCount >= (this.challenge?.logoutUrls?.length || 0)) {
            // All done, submit the form
            const submitEvent = new SubmitEvent("submit");
            this.submitForm(submitEvent);
        }
    }

    protected renderProgress(): TemplateResult {
        const total = this.challenge?.logoutUrls?.length || 0;
        const percentage = total > 0 ? Math.round((this.completedCount / total) * 100) : 0;

        return html`
            <div class="pf-c-progress">
                <div class="pf-c-progress__description">${msg("Logging out of providers...")}</div>
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

    public override render(): TemplateResult {
        // If no logout URLs, stage may have gotten double injected
        if (!this.challenge?.logoutUrls || !this.challenge.logoutUrls.length) {
            const submitEvent = new SubmitEvent("submit");
            this.submitForm(submitEvent);
            return html`<ak-flow-card .challenge=${this.challenge} loading></ak-flow-card>`;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Single Logout")}</span>
            <form class="pf-c-form">
                <div class="pf-c-form__group">${this.renderProgress()}</div>
                <div class="pf-c-form__group">
                    ${this.logoutStatuses.map(
                        (status) => html`
                            <div class="provider-status">
                                ${renderStatusIcon(status.status)}
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
        "ak-provider-iframe-logout": IFrameLogoutStage;
    }
}
