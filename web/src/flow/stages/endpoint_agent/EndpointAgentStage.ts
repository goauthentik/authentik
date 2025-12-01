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
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-stage-endpoint-agent")
export class EndpointAgentStage extends BaseStage<
    EndpointAgentChallenge,
    EndpointAgentChallengeResponseRequest
> {
    static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, css``];

    firstUpdated() {
        window.addEventListener("message", (ev) => {
            if (ev.data?._ak_ext === "authentik-platform-sso") {
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
    }

    updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            window.postMessage({
                _ak_ext: "authentik-platform-sso",
                challenge: this.challenge,
            });
        }
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <ak-empty-state loading
                ><span>${msg("Verifying your device...")}</span>
            </ak-empty-state>
        </ak-flow-card>`;
    }
}
