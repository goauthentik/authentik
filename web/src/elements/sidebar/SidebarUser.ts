import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import fa from "@fortawesome/fontawesome-free/css/all.css";
// @ts-ignore
import AvatarStyle from "@patternfly/patternfly/components/Avatar/avatar.css";
import { User } from "../../api/user";

@customElement("pb-sidebar-user")
export class SidebarUser extends LitElement {
    @property()
    user?: User;

    static get styles(): CSSResult[] {
        return [
            fa,
            NavStyle,
            AvatarStyle,
            css`
                :host {
                    display: flex;
                    width: 100%;
                    flex-direction: row;
                    justify-content: space-between;
                }
                .pf-c-nav__link {
                    align-items: center;
                }
                .user-avatar {
                    display: flex;
                    flex-direction: row;
                }
                .user-avatar > span {
                    line-height: var(--pf-c-avatar--Height);
                    padding-left: var(--pf-global--spacer--sm);
                    font-size: var(--pf-global--FontSize--lg);
                }
                .user-logout {
                    flex-shrink: 3;
                    max-width: 75px;
                }
            `,
        ];
    }

    render(): TemplateResult {
        if (!this.user) {
            return html``;
        }
        return html`
            <a href="#/-/user/" class="pf-c-nav__link user-avatar" id="user-settings">
                <img class="pf-c-avatar" src="${this.user?.avatar}" alt="" />
                <span>${this.user?.username}</span>
            </a>
            <a href="/flows/-/default/invalidation/" class="pf-c-nav__link user-logout" id="logout">
                <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
            </a>
        `;
    }
}
