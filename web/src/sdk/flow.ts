import "@goauthentik/elements/messages/MessageContainer";
import { FlowExecutor } from "@goauthentik/flow/FlowExecutor";
// Statically import some stages to speed up load speed
import "@goauthentik/flow/stages/access_denied/AccessDeniedStage";
// Import webauthn-related stages to prevent issues on safari
// Which is overly sensitive to allowing things only in the context of a
// user interaction
import "@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage";
import "@goauthentik/flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "@goauthentik/flow/stages/autosubmit/AutosubmitStage";
import "@goauthentik/flow/stages/captcha/CaptchaStage";
import "@goauthentik/flow/stages/identification/IdentificationStage";
import "@goauthentik/flow/stages/password/PasswordStage";
import "@goauthentik/sdk/common";
// end of stage import

import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { until } from "lit/directives/until.js";


@customElement("ak-embedded-flow-executor")
export class EmbeddedFlowExecutor extends FlowExecutor {
    renderCard() {
        return html`<div class="pf-c-login">
            <div class="pf-c-login__main">
                ${this.loading && this.challenge
                    ? html`<ak-loading-overlay></ak-loading-overlay>`
                    : nothing}
                ${until(this.renderChallenge())}
            </div>
        </div>`;
    }
}
