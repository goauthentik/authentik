import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { writeToClipboard } from "#common/clipboard";

import { Form } from "#elements/forms/Form";

import { CoreApi, Link, User, UserRecoveryLinkRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-recovery-link-form")
export class UserRecoveryLinkForm extends Form<UserRecoveryLinkRequest> {
    @property({ attribute: false })
    user!: User;

    async send(data: UserRecoveryLinkRequest): Promise<Link> {
        const response = await new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryCreate({
            id: this.user.pk,
            userRecoveryLinkRequest: data,
        });

        await writeToClipboard(response.link, msg("Recovery link"));

        return response;
    }

    renderForm(): TemplateResult {
        return html`
            <ak-text-input
                name="tokenDuration"
                label=${msg("Token duration")}
                value="days=1"
                .bighelp=${html`<p class="pf-c-form__helper-text">
                    ${msg("If a recovery token already exists, its duration is updated.")}
                </p>`}
            >
            </ak-text-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-recovery-link-form": UserRecoveryLinkForm;
    }
}
