import { AKElement } from "#elements/Base";
import { isDefaultAvatar } from "#elements/utils/images";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

@customElement("ak-form-static")
export class FormStatic extends AKElement {
    public override role = "banner";
    public override ariaLabel = msg("User information");

    @property()
    userAvatar?: string;

    @property()
    user?: string;

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

    render() {
        if (!this.user) {
            return nothing;
        }

        return html`
            <div class="primary-content">
                ${this.userAvatar && !isDefaultAvatar(this.userAvatar)
                    ? html`<img
                          class="pf-c-avatar"
                          src=${this.userAvatar}
                          alt=${this.user ? msg(str`Avatar for ${this.user}`) : msg("User avatar")}
                      />`
                    : nothing}
                <div class="username" aria-description=${msg("Username")}>${this.user}</div>
            </div>
            <div class="links">
                <slot name="link"></slot>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-form-static": FormStatic;
    }
}
