import "#elements/EmptyState";
import "#flow/FormStatic";
import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import { EndpointAgentChallenge, EndpointAgentChallengeResponseRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-stage-endpoint-agent")
export class EndpointAgentStage extends BaseStage<
    EndpointAgentChallenge,
    EndpointAgentChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFTitle, css``];

    firstUpdated() {
        window.addEventListener("message", (ev) => {
            if (ev.data?._ak_ext === "authentik-platform-sso" && ev.data.response) {
                this.host?.submit(
                    {
                        response: ev.data?.response,
                    } as EndpointAgentChallengeResponseRequest,
                    {
                        invisible: true,
                    },
                );
            }
        });

        const delay = this.challenge?.challengeIdleTimeout ?? 3000;

        // Fallback in case we don't get a response
        setTimeout(() => {
            this.host?.submit(
                {
                    response: null,
                } as EndpointAgentChallengeResponseRequest,
                {
                    invisible: true,
                },
            );
        }, delay);
    }

    updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge) {
            if (this.challenge.responseErrors) {
                return;
            }
            window.postMessage({
                _ak_ext: "authentik-platform-sso",
                challenge: this.challenge.challenge,
            });
        }
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            ${this.challenge?.responseErrors
                ? html`
                      <ak-empty-state icon="fa-times"
                          ><span>${msg("Failed to validate device.")}</span>
                          <div slot="body">
                              ${this.challenge.responseErrors.response.map((err) => {
                                  return html`<p>${err.string}</p>`;
                              })}
                          </div>
                      </ak-empty-state>
                  `
                : html` <ak-empty-state loading
                      ><span>${msg("Verifying your device...")}</span>
                  </ak-empty-state>`}
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-endpoint-agent": EndpointAgentStage;
    }
}
