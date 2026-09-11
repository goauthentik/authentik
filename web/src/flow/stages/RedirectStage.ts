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
import { css, CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-redirect")
export class RedirectStage extends BaseStage<RedirectChallenge, FlowChallengeResponseRequest> {
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

            /* The spinner and the manual form share one grid cell, so the form is laid
             * out from the first paint and the two cross-fade without moving anything. */
            .redirect-pending {
                display: grid;
            }

            .redirect-pending > * {
                grid-area: 1 / 1;
            }

            .redirect-spinner {
                place-self: center;
                animation: ak-redirect-conceal 150ms linear 2s forwards;
            }

            .redirect-fallback {
                opacity: 0;
                animation: ak-redirect-reveal 150ms linear 2s forwards;
            }

            @keyframes ak-redirect-reveal {
                to {
                    opacity: 1;
                }
            }

            @keyframes ak-redirect-conceal {
                to {
                    opacity: 0;
                }
            }

            /* The delay is what tells the user the redirect is stuck, so it stays. Only
             * the fade itself is decorative. */
            @media (prefers-reduced-motion: reduce) {
                .redirect-spinner,
                .redirect-fallback {
                    animation-duration: 1ms;
                }
            }
        `,
    ];

    getURL(): string {
        return new URL(this.challenge?.to || "", document.baseURI).toString();
    }

    // The current implementation expects the button and the stage to share the same DOM context,
    // and the same rootNode. If that changes, this will need to be updated.
    get promptUser() {
        return !!(this.getRootNode() as Element | undefined)?.querySelector(
            "ak-flow-inspector-button",
        )?.open;
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
    }

    /**
     * Exit bookkeeping for the manual anchor, which navigates natively so that the click's user
     * gesture reaches the browser. `redirect()` is not reused here: it can await tab orchestration
     * first, and a `window.location.assign` after that no longer carries the gesture.
     */
    followRedirect(): void {
        const finalRedirect = this.challenge?.finalRedirect ?? false;
        const url = new URL(this.challenge!.to, window.location.origin);

        // A foreign final redirect lets the navigation's `pagehide` broadcast the exit; every
        // other target is a same-origin hop, so suppress it.
        if (!(finalRedirect && url.origin !== window.location.origin)) {
            suppressNextExitForSameOriginNavigation();
        }
    }

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

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

        // With the flow inspector open the redirect waits for the user, so the form is the whole
        // point and is shown right away. Otherwise the redirect runs on its own and the form is
        // only a fallback, so a spinner covers it until the redirect has had time to happen.
        //
        // The fallback is always rendered, and the spinner covering it is uncovered by a CSS
        // animation rather than a timer. Embedded WebViews that block the script-initiated,
        // gesture-less navigation (Google's account-setup "MinuteMaid" WebView, gh#23660) stop
        // running this page's timers once they do. Measured against Android WebView, animations
        // keep running there, so the reveal must not depend on JavaScript.
        const automatic = !this.promptUser;

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Redirect")}</span>
            <div class=${classMap({ "redirect-pending": automatic })}>
                ${automatic
                    ? html`<ak-empty-state
                          class="redirect-spinner"
                          loading
                          default-label
                      ></ak-empty-state>`
                    : nothing}
                <form class=${classMap({ "pf-c-form": true, "redirect-fallback": automatic })}>
                    <div class="pf-c-form__group">
                        <p>${msg("You're about to be redirected to the following URL.")}</p>
                        <code>${this.getURL()}</code>
                    </div>
                    <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
                        <legend class="sr-only">${msg("Form actions")}</legend>
                        <a
                            class="pf-c-button pf-m-primary pf-m-block"
                            href=${this.challenge.to}
                            @click=${() => this.followRedirect()}
                        >
                            ${msg("Follow redirect")}
                        </a>
                    </fieldset>
                </form>
            </div>
        </ak-flow-card>`;
    }
}

export default RedirectStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect": RedirectStage;
    }
}
