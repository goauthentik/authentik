import "#elements/EmptyState";
import "#flow/components/ak-flow-card";

import { globalAK } from "#common/global";

import { BaseStage } from "#flow/stages/base";

import {
    BskyAuthenticationChallenge,
    BskyAuthenticationChallengeResultRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-flow-source-bsky")
export class BskyLoginInit extends BaseStage<
    BskyAuthenticationChallenge,
    BskyAuthenticationChallengeResultRequest
> {
    @state()
    handle = "";

    static styles: CSSResult[] = [PFLogin, PFForm, PFFormControl, PFButton, PFTitle];

    startLogin(): void {
        const slug = this.challenge?.slug || "";
        const url = `${globalAK().api.base}source/bsky/${slug}/login/?identifier=${encodeURIComponent(this.handle)}`;
        window.location.assign(url);
    }

    render(): TemplateResult {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Sign in with Bluesky")}</span>
            <form
                class="pf-c-form"
                @submit=${(e: SubmitEvent) => {
                    e.preventDefault();
                    this.startLogin();
                }}
            >
                <div class="pf-c-form__group">
                    <label class="pf-c-form__label" for="bsky-handle">
                        ${msg("Bluesky handle")}
                    </label>
                    <input
                        type="text"
                        id="bsky-handle"
                        class="pf-c-form-control"
                        placeholder="you.bsky.social"
                        required
                        .value=${this.handle}
                        @input=${(e: InputEvent) => {
                            this.handle = (e.target as HTMLInputElement).value;
                        }}
                    />
                </div>
                <button class="pf-c-button pf-m-primary pf-m-block" type="submit">
                    ${msg("Continue")}
                </button>
            </form>
        </ak-flow-card>`;
    }
}

export default BskyLoginInit;

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-source-bsky": BskyLoginInit;
    }
}
