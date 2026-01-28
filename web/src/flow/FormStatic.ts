import { AKElement } from "#elements/Base";
import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { isDefaultAvatar } from "#elements/utils/images";

import {
    AccessDeniedChallenge,
    AuthenticatorDuoChallenge,
    AuthenticatorEmailChallenge,
    AuthenticatorStaticChallenge,
    AuthenticatorTOTPChallenge,
    AuthenticatorWebAuthnChallenge,
    CaptchaChallenge,
    ConsentChallenge,
    PasswordChallenge,
    SessionEndChallenge,
    UserLoginChallenge,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

@customElement("ak-form-static")
export class AKFormStatic extends AKElement {
    public override role = "banner";
    public override ariaLabel = msg("User information");

    @property({ type: String })
    public avatar: string = "";

    @property({ type: String })
    public username: string = "";

    static styles: CSSResult[] = [
        PFAvatar,
        css`
            :host {
                margin-block-start: var(--pf-global--spacer--sm);
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-flow: wrap;
                gap: var(--pf-global--spacer--sm);
            }

            .pf-c-avatar {
                flex: 0 0 auto;
            }

            .primary-content {
                display: flex;
                align-items: center;
                flex: 1 1 auto;
                gap: var(--pf-global--spacer--md);
            }

            .username {
                flex: 1 1 auto;
                text-align: left;
                max-width: 20rem;
                text-overflow: ellipsis;
                overflow-wrap: break-word;

                display: box;
                display: -webkit-box;
                line-clamp: 3;
                -webkit-line-clamp: 3;
                box-orient: vertical;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }

            .links {
                flex: 0 0 auto;
                text-align: right;
            }
        `,
    ];

    protected override render() {
        if (!this.username) {
            return nothing;
        }

        return html`
            <div class="primary-content">
                ${this.avatar && !isDefaultAvatar(this.avatar)
                    ? html`<img
                          class="pf-c-avatar"
                          src=${this.avatar}
                          alt=${this.username
                              ? msg(str`Avatar for ${this.username}`, {
                                    id: "avatar.alt-text-for-user",
                                })
                              : msg("User avatar", {
                                    id: "avatar.alt-text",
                                })}
                      />`
                    : nothing}
                <div class="username" aria-description=${msg("Username")}>${this.username}</div>
            </div>
            <div class="links">
                <slot name="link"></slot>
            </div>
        `;
    }
}

/**
 * @internal
 */
export type FormStaticChallenge =
    | SessionEndChallenge
    | AccessDeniedChallenge
    | AuthenticatorDuoChallenge
    | AuthenticatorEmailChallenge
    | AuthenticatorStaticChallenge
    | AuthenticatorTOTPChallenge
    | AuthenticatorWebAuthnChallenge
    | CaptchaChallenge
    | ConsentChallenge
    | PasswordChallenge
    | UserLoginChallenge;

export interface FlowUserDetailsProps {
    challenge?: Partial<
        Pick<FormStaticChallenge, "pendingUserAvatar" | "pendingUser" | "flowInfo">
    > | null;
}

export const FlowUserDetails: LitFC<FlowUserDetailsProps> = ({ challenge }) => {
    const { pendingUserAvatar, pendingUser, flowInfo } = challenge || {};
    return guard(
        [pendingUserAvatar, pendingUser, flowInfo],
        () =>
            html`<ak-form-static
                class="pf-c-form__group"
                avatar=${ifPresent(pendingUserAvatar)}
                username=${ifPresent(pendingUser)}
            >
                ${flowInfo?.cancelUrl
                    ? html`
                          <div slot="link">
                              <a href=${flowInfo.cancelUrl}>${msg("Not you?")}</a>
                          </div>
                      `
                    : nothing}
            </ak-form-static>`,
    );
};

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-static": AKFormStatic;
    }
}
