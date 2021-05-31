import "./locale";
import "../elements/messages/MessageContainer";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { t } from "@lingui/macro";

import Carbon from "carbon-components/css/carbon-components.min.css";
import "carbon-web-components/es/components/ui-shell/header";
import "carbon-web-components/es/components/ui-shell/header-name";
import "carbon-web-components/es/components/ui-shell/header-nav";
import "carbon-web-components/es/components/ui-shell/header-nav-item";
import "carbon-web-components/es/components/ui-shell/side-nav";
import "carbon-web-components/es/components/ui-shell/side-nav-items";
import "carbon-web-components/es/components/ui-shell/side-nav-link";
import "carbon-web-components/es/components/button/button";

import { CurrentTenant } from "authentik-api";
import { DefaultTenant } from "../elements/sidebar/SidebarBrand";
import { tenant } from "../api/Config";
import { configureSentry } from "../api/Sentry";
import { ROUTES } from "../routes_user";
import "../elements/router/RouterOutlet";
import { until } from "lit-html/directives/until";
import { me } from "../api/Users";

@customElement("ak-interface-user")
export class UserInterface extends LitElement {

    @property({ attribute: false })
    tenant: CurrentTenant = DefaultTenant;

    static get styles(): CSSResult[] {
        return [Carbon, css`
            bx-header-name img {
                max-height: 100%;
                width: 200px;
                padding: 6px 0;
            }
            bx-header-nav-item.avatar img {
                max-height: 50px;
                padding: 0;
            }
            #main-content {
                display: flex;
                flex-direction: column;
                align-items: center;
                position: relative;
            }
            .bx--content {
                margin-top: 3rem;
                height: calc(100vh - 3em - 3em);
                width: 100%;
            }
        `];
    }

    firstUpdated(): void {
        configureSentry(true);
        tenant().then(tenant => this.tenant = tenant);
    }

    render(): TemplateResult {
        return html`
            <div id="main-content" class="bx--body" role="none">
                <bx-header role="banner">
                    <bx-header-name href="#/">
                        <img src="${this.tenant.brandingLogo}" alt="authentik icon" loading="lazy" />
                    </bx-header-name>
                    <div class="bx--header__global">
                        ${until(me().then((u) => {
                            if (u.user.isSuperuser) {
                                return html`<bx-header-nav-item href="../admin" class="bx--btn--primary">
                                    ${t`Admin`}
                                </bx-header-nav-item>`;
                            }
                            return html``;
                        }), html``)}
                        <bx-header-nav-item class="avatar" href="#/user">
                            ${until(me().then((u) => {
                                return html`<img src="${u.user.avatar}" alt="" />`;
                            }), html``)}
                        </bx-header-nav-item>
                        <bx-header-nav-item href="/flows/-/default/invalidation/">
                            ${t`Logout`}
                        </bx-header-nav-item>
                    </div>
                </bx-header>
                <ak-router-outlet .routes=${ROUTES} role="main" class="bx--content" tabindex="-1" defaultUrl="/library">
                </ak-router-outlet>
            </div>`;
    }

}
