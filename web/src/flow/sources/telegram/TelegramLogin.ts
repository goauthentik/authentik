import { loadTelegramWidget, TelegramUserResponse } from "./utils";

import { BaseStage } from "#flow/stages/base";

import { TelegramChallengeResponseRequest, TelegramLoginChallenge } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-flow-source-telegram")
export class TelegramLogin extends BaseStage<
    TelegramLoginChallenge,
    TelegramChallengeResponseRequest
> {
    btnRef = createRef();

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle, PFDivider];
    }

    firstUpdated(): void {
        loadTelegramWidget(
            this.btnRef.value,
            this.challenge.botUsername,
            this.challenge.requestMessageAccess,
            (user: TelegramUserResponse) => {
                this.host.submit({
                    id: user.id,
                    authDate: user.auth_date,
                    hash: user.hash,
                    firstName: user.first_name,
                    lastName: user.last_name,
                    username: user.username,
                    photoUrl: user.photo_url,
                });
            },
        );
    }

    render(): TemplateResult {
        return html` <ak-flow-card .challenge=${this.challenge}>
            <span slot="title">${msg("Authenticating with Telegram...")}</span>
            <form class="pf-c-form">
                <hr class="pf-c-divider" />
                <p>${msg("Click the button below to start.")}</p>

                <div ${ref(this.btnRef)}></div>
            </form>
        </ak-flow-card>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-source-telegram": TelegramLogin;
    }
}
