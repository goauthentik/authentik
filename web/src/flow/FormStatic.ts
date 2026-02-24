import { AKElement } from "#elements/Base";
import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";
import { isDefaultAvatar } from "#elements/utils/images";

import Styles from "#flow/FormStatic.css";
import { StageChallengeLike } from "#flow/types";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

@customElement("ak-form-static")
export class AKFormStatic extends AKElement {
    static styles = [PFAvatar, Styles];

    public override role = "banner";
    public override ariaLabel = msg("User information");

    @property({ type: String })
    public avatar: string = "";

    @property({ type: String })
    public username: string = "";

    protected renderAvatar(avatar: string, username: string) {
        return html`<img
            class="pf-c-avatar"
            src=${avatar}
            alt=${msg(str`Avatar for ${username}`, {
                id: "avatar.alt-text-for-user",
            })}
        />`;
    }

    protected renderContent(username: string, avatar?: string) {
        const withAvatar = avatar && !isDefaultAvatar(avatar);
        return html`
            <div class="primary-content">
                ${withAvatar ? this.renderAvatar(avatar, username) : nothing}
                <div class="username" aria-description=${msg("Username")}>${username}</div>
            </div>
            <div class="links">
                <slot name="link"></slot>
            </div>
        `;
    }

    protected override render() {
        const { username, avatar } = this;
        return username ? this.renderContent(username, avatar) : nothing;
    }
}

export interface FlowUserDetailsProps {
    challenge?: StageChallengeLike | null;
}

export const FlowUserDetails: LitFC<FlowUserDetailsProps> = ({ challenge }) => {
    const { pendingUserAvatar, pendingUser, flowInfo } = challenge || {};
    return html`<ak-form-static
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
    </ak-form-static>`;
};

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-static": AKFormStatic;
    }
}
