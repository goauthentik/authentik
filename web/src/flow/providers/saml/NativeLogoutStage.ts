import "#flow/components/ak-flow-card";

import { BaseStage } from "#flow/stages/base";

import {
    FlowChallengeResponseRequest,
    NativeLogoutChallenge,
    SpBindingEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { createRef, ref, Ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-provider-saml-native-logout")
export class NativeLogoutStage extends BaseStage<
    NativeLogoutChallenge,
    FlowChallengeResponseRequest
> {
    #formRef: Ref<HTMLFormElement> = createRef();

    public static styles: CSSResult[] = [PFBase, PFLogin, PFForm, PFButton, PFFormControl, PFTitle];

    public override firstUpdated(changedProperties: PropertyValues): void {
        super.firstUpdated(changedProperties);

        // If complete, auto-submit to continue flow
        if (this.challenge.isComplete) {
            const submitEvent = new SubmitEvent("submit");
            this.submitForm(submitEvent);
            return;
        }

        // If POST binding, auto-submit the form
        if (this.challenge.binding === SpBindingEnum.Post && this.#formRef.value) {
            this.#formRef.value.submit();
        }

        // If redirect binding, perform the redirect
        if (this.challenge.binding === SpBindingEnum.Redirect) {
            if (!this.challenge.redirectUrl) {
                throw new TypeError(`Binding challenge does not a have a redirect URL`);
            }
            requestAnimationFrame(() => window.location.assign(this.challenge.redirectUrl!));
        }
    }

    render(): TemplateResult {
        const providerName = this.challenge.providerName || msg("SAML Provider");

        // For complete state, just show loading (will auto-submit)
        if (this.challenge.isComplete) {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg("SAML logout complete")}</span>
            </ak-flow-card>`;
        }

        // For redirect binding, just show loading and firstUpdated will redirect for us
        if (this.challenge.binding === SpBindingEnum.Redirect) {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title">${msg(str`Redirecting to SAML provider: ${providerName}`)}</span>
            </ak-flow-card>`;
        }

        if (this.challenge.binding !== SpBindingEnum.Post) {
            throw new TypeError(`Unknown challenge binding type ${this.challenge.binding}`);
        }

        // For POST binding, render auto-submit form
        if (this.challenge.binding === SpBindingEnum.Post) {
            return html`<ak-flow-card .challenge=${this.challenge} loading>
                <span slot="title"
                    >${msg(str`Posting logout request to SAML provider: ${providerName}`)}</span
                >
                <form
                    class="pf-c-form"
                    action="${ifDefined(this.challenge.postUrl)}"
                    method="post"
                    ${ref(this.#formRef)}
                >
                    <input
                        type="hidden"
                        name="SAMLRequest"
                        value="${ifDefined(this.challenge.samlRequest)}"
                    />
                    ${this.challenge.relayState
                        ? html`<input
                              type="hidden"
                              name="RelayState"
                              value="${this.challenge.relayState}"
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
