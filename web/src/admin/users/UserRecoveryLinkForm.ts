import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";
import { writeToClipboard } from "#elements/utils/writeToClipboard";

import { CoreApi, CoreUsersRecoveryCreateRequest, Link, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-recovery-link-form")
export class UserRecoveryLinkForm extends Form<CoreUsersRecoveryCreateRequest> {
    @property({ attribute: false })
    user!: User;

    async send(data: CoreUsersRecoveryCreateRequest): Promise<Link> {
        data.id = this.user.pk;
        const response = await new CoreApi(DEFAULT_CONFIG).coreUsersRecoveryCreate(data);

        const wroteToClipboard = await writeToClipboard(response.link);
        if (wroteToClipboard) {
            this.successMessage = msg(
                str`A copy of this recovery link has been placed in your clipboard: ${response.link}`,
            );
        } else {
            this.successMessage = msg(
                str`authentik does not have access to your clipboard, please copy the recovery link manually: ${response.link}`,
            );
        }

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
