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

type TelegramUserResponse = {
    id: number;
    first_name?: string;
    last_name?: string;
    username?: string;
    photo_url?: string;
    auth_date: number;
    hash: string;
};

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
        const widgetScript = document.createElement("script");
        widgetScript.src = "https://telegram.org/js/telegram-widget.js?22";
        widgetScript.type = "text/javascript";
        widgetScript.setAttribute("data-radius", "0");
        widgetScript.setAttribute("data-telegram-login", this.challenge.botUsername);
        if (this.challenge.requestAccess) {
            widgetScript.setAttribute("data-request-access", "write");
        }
        const callbackName =
            "__ak_telegram_login_callback_" + (Math.random() + 1).toString(36).substring(7);
        (window as unknown as Record<string, (user: TelegramUserResponse) => void>)[callbackName] =
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
            };
        widgetScript.setAttribute("data-onauth", callbackName + "(user)");
        this.btnRef.value?.appendChild(widgetScript);
        widgetScript.onload = () => {
            if (widgetScript.previousSibling) {
                this.btnRef.value?.appendChild(widgetScript.previousSibling);
            }
        };
        document.body.append(widgetScript);
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
