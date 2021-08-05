import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import { me } from "../../api/Users";
import { until } from "lit-html/directives/until";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-sidebar-user")
export class SidebarUser extends LitElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFNav,
            PFAvatar,
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
            <a href="#/user" class="pf-c-nav__link user-avatar" id="user-settings">
                ${until(
                    me().then((u) => {
                        return html`<img
                            class="pf-c-avatar"
                            src="${ifDefined(u.user.avatar)}"
                            alt=""
                        />`;
                    }),
                    html``,
                )}
            </a>
            <a href="/flows/-/default/invalidation/" class="pf-c-nav__link user-logout" id="logout">
                <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
            </a>
        `;
    }
}
