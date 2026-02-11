import "#flow/components/ak-flow-card";

import { SlottedTemplateResult } from "#elements/types";

import { BaseStage } from "#flow/stages/base";

import {
    FlowChallengeResponseRequest,
    NativeLogoutChallenge,
    SAMLBindingsEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-provider-saml-native-logout")
export class NativeLogoutStage extends BaseStage<
    NativeLogoutChallenge,
    FlowChallengeResponseRequest
> {
    #formRef: Ref<HTMLFormElement> = createRef();

    public static styles: CSSResult[] = [PFLogin, PFForm, PFButton, PFFormControl, PFTitle];

    public override firstUpdated(changedProperties: PropertyValues): void {
        super.firstUpdated(changedProperties);

        if (!this.challenge) {
            return;
        }

        // If complete, auto-submit to continue flow
        if (this.challenge.isComplete) {
            const submitEvent = new SubmitEvent("submit");
            this.submitForm(submitEvent);
            return;
        }

        // If POST binding, auto-submit the form
        if (this.challenge.samlBinding === SAMLBindingsEnum.Post && this.#formRef.value) {
            this.#formRef.value.submit();
        }

        // If redirect binding, perform the redirect
        if (this.challenge.samlBinding === SAMLBindingsEnum.Redirect) {
            if (!this.challenge.redirectUrl) {
                throw new TypeError(`Binding challenge does not a have a redirect URL`);
            }
            requestAnimationFrame(() => {
                if (!this.challenge?.redirectUrl) return;

                return window.location.assign(this.challenge.redirectUrl!);
            });
        }
    }

    protected render(): SlottedTemplateResult {
        if (!this.challenge) {
            return nothing;
        }

        const providerName = this.challenge.providerName || msg("SAML Provider");

        // For complete state, just show loading (will auto-submit)
        if (this.challenge.isComplete) {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg("SAML logout complete")}</span>
            </ak-flow-card>`;
        }

        // For redirect binding, just show loading and firstUpdated will redirect for us
        if (this.challenge.samlBinding === SAMLBindingsEnum.Redirect) {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg(str`Redirecting to SAML provider: ${providerName}`)}</span>
            </ak-flow-card>`;
        }

        if (this.challenge.samlBinding !== SAMLBindingsEnum.Post) {
            throw new TypeError(`Unknown challenge binding type ${this.challenge.samlBinding}`);
        }

        // For POST binding, render auto-submit form
        if (this.challenge.samlBinding === SAMLBindingsEnum.Post) {
            const title = this.challenge.samlResponse
                ? msg(str`Posting logout response to SAML provider: ${providerName}`)
                : msg(str`Posting logout request to SAML provider: ${providerName}`);
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${title}</span>
                <form
                    class="pf-c-form"
                    action="${ifDefined(this.challenge.postUrl)}"
                    method="post"
                    ${ref(this.#formRef)}
                >
                    ${this.challenge.samlRequest
                        ? html`<input
                              type="hidden"
                              name="SAMLRequest"
                              value="${this.challenge.samlRequest}"
                          />`
                        : nothing}
                    ${this.challenge.samlResponse
                        ? html`<input
                              type="hidden"
                              name="SAMLResponse"
                              value="${this.challenge.samlResponse}"
                          />`
                        : nothing}
                    ${this.challenge.samlRelayState
                        ? html`<input
                              type="hidden"
                              name="RelayState"
                              value="${this.challenge.samlRelayState}"
                          />`
                        : nothing}
                </form>
            </ak-flow-card>`;
        }

        // Default case - should not happen but TypeScript needs this
        return html`<ak-flow-card .challenge=${this.challenge} loading></ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-native-logout": NativeLogoutStage;
    }
}
