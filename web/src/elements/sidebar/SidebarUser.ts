import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import fa from "@fortawesome/fontawesome-free/css/all.css";
// @ts-ignore
import AvatarStyle from "@patternfly/patternfly/components/Avatar/avatar.css";
import { User } from "../../api/Users";
import { until } from "lit-html/directives/until";

import "../notifications/NotificationTrigger";

@customElement("ak-sidebar-user")
export class SidebarUser extends LitElement {

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
                    display: flex;
                    justify-content: center;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`
            <a href="#/-/user/" class="pf-c-nav__link user-avatar" id="user-settings">
                ${until(User.me().then(u => {
        return html`<img class="pf-c-avatar" src="${u.avatar}" alt="" />`;}), html``)}
            </a>
            <ak-notification-trigger class="pf-c-nav__link user-notifications">
                <i class="fas fa-bell pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </ak-notification-trigger>
            <a href="/flows/-/default/invalidation/" class="pf-c-nav__link user-logout" id="logout">
                <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
            </a>
        `;
    }
}
