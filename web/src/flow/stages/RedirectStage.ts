import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { BaseStage } from "#flow/stages/base";
import {
    multiTabOrchestrateLeave,
    multiTabOrchestrateResume,
    suppressNextExitForSameOriginNavigation,
} from "#flow/tabs/orchestrator";

import { FlowChallengeResponseRequest, RedirectChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

/**
 * How long to wait after starting the automatic redirect before revealing the
 * manual fallback. In a normal browser the navigation commits and this component
 * is torn down long before this fires; if we're still alive afterwards the
 * automatic navigation was most likely blocked.
 */
const MANUAL_FALLBACK_DELAY_MS = 2000;

@customElement("ak-stage-redirect")
export class RedirectStage extends BaseStage<RedirectChallenge, FlowChallengeResponseRequest> {
    @property({ type: Boolean })
    promptUser = false;

    @state()
    startedRedirect = false;

    /**
     * Revealed when the automatic redirect appears to have been blocked by the
     * environment. Some embedded WebViews (notably Google's account-setup
     * "MinuteMaid" WebView, gh#23660) veto script-initiated, gesture-less
     * top-level navigation, so `window.location.assign` silently does nothing
     * and the flow hangs on the spinner. Exposing an anchor the user activates
     * makes the navigation carry  user gesture, which such WebViews honor.
     */
    @state()
    showManualFallback = false;

    #fallbackTimer?: ReturnType<typeof setTimeout>;

    disconnectedCallback(): void {
        super.disconnectedCallback();
        clearTimeout(this.#fallbackTimer);
    }

    static styles: CSSResult[] = [
        PFLogin,
        PFForm,
        PFButton,
        PFFormControl,
        PFTitle,
        css`
            code {
                word-break: break-all;
            }
        `,
    ];

    getURL(): string {
        return new URL(this.challenge?.to || "", document.baseURI).toString();
    }

    updated(changed: PropertyValues<this>): void {
        super.updated(changed);

        if (!changed.has("challenge")) {
            return;
        }
        if (this.promptUser) {
            document.addEventListener("keydown", (ev) => {
                if (ev.key === "Enter") {
                    this.redirect();
                }
            });
            return;
        }
        this.redirect();
    }

    async redirect() {
        console.debug(
            "authentik/stages/redirect: redirecting to url from server",
            this.challenge?.to,
        );

        // `final_redirect` marks the terminal redirect out of a completed flow. Only then do we
        // resume other continuous-login tabs; intermediate hops (source stages, the same-origin
        // SAML resume re-entry) skip orchestration entirely.
        const finalRedirect = this.challenge?.finalRedirect ?? false;
        if (finalRedirect) {
            await multiTabOrchestrateResume();
        }

        // A foreign final redirect means we're leaving authentik for good, so signal our exit.
        // Same-origin navigation suppress it, otherwise we'd look like we left mid-flow.
        const url = new URL(this.challenge!.to, window.location.origin);

        if (finalRedirect && url.origin !== window.location.origin) {
            multiTabOrchestrateLeave();
        } else {
            suppressNextExitForSameOriginNavigation();
        }

        window.location.assign(this.challenge!.to);
        this.startedRedirect = true;

        // If the automatic navigation was silently blocked, this component is still
        // alive after the delay -> reveal the manual fallback so the user can complete
        // the redirect with a gesture-carrying activation
        // Custom-scheme targets keep their own "you may close this" message.
        if (url.protocol.startsWith("http")) {
            this.#fallbackTimer = setTimeout(() => {
                this.showManualFallback = true;
            }, MANUAL_FALLBACK_DELAY_MS);
        }
    }

    renderLoading(): TemplateResult {
        const url = new URL(this.getURL());
        // If the protocol isn't http or https assume a custom protocol, that has an OS-level
        // handler, which the browser will show a popup for.
        // As this wouldn't really be a redirect, show a message that the page can be closed
        // and try to close it ourselves
        if (!url.protocol.startsWith("http")) {
            return html`<ak-flow-card .challenge=${this.challenge}>
                <ak-empty-state icon="fas fa-check"
                    ><span>${msg("You may close this page now.")}</span>
                </ak-empty-state>
            </ak-flow-card>`;
        }
        return html`<ak-flow-card .challenge=${this.challenge} loading></ak-flow-card>`;
    }

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        // Show the manual "Follow redirect" when the flow inspector is open
        // (promptUser) or when the automatic redirect appears to have been blocked
        // (showManualFallback). Otherwise keep showing the loading spinner while the
        // automatic redirect proceeds.
        const showManual = (this.promptUser && !this.startedRedirect) || this.showManualFallback;
        if (!showManual) {
            return this.renderLoading();
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Redirect")}</span>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <p>${msg("You're about to be redirect to the following URL.")}</p>
                    <code>${this.getURL()}</code>
                </div>
                <fieldset class="pf-c-form__group pf-m-action">
                    <legend class="sr-only">${msg("Form actions")}</legend>
                    <a
                        type="submit"
                        class="pf-c-button pf-m-primary pf-m-block"
                        href=${this.challenge.to}
                        @click=${(ev: Event) => {
                            ev.preventDefault();
                            this.redirect();
                        }}
                    >
                        ${msg("Follow redirect")}
                    </a>
                </fieldset>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect": RedirectStage;
    }
}
