import "#flow/components/ak-flow-card";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

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
import { customElement, state } from "lit/decorators.js";

@customElement("ak-stage-redirect")
export class RedirectStage extends BaseStage<RedirectChallenge, FlowChallengeResponseRequest> {
    @state()
    startedRedirect = false;

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
        this.startedRedirect = true;
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
        if (this.startedRedirect || !this.promptUser) {
            return this.renderLoading();
        }

        if (!this.challenge) {
            return nothing;
        }

        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Redirect")}</span>
            <form class="pf-c-form">
                <div class="pf-c-form__group">
                    <p>${msg("You're about to be redirected to the following URL.")}</p>
                    <code>${this.getURL()}</code>
                </div>
                <fieldset class="ak-c-fieldset pf-c-form__group pf-m-action">
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

export default RedirectStage;

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect": RedirectStage;
    }
}
