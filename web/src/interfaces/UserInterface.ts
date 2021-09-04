import "./locale";
import "../elements/messages/MessageContainer";
import {
    css,
    CSSResult,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
import { t } from "@lingui/macro";

import { CurrentTenant } from "@goauthentik/api";
import { DefaultTenant } from "../elements/sidebar/SidebarBrand";
import { tenant } from "../api/Config";
import { configureSentry } from "../api/Sentry";
import { ROUTES } from "../routesUser";
import "../elements/router/RouterOutlet";

@customElement("ak-interface-user")
export class UserInterface extends LitElement {
    @property({ attribute: false })
    tenant: CurrentTenant = DefaultTenant;

    firstUpdated(): void {
        configureSentry(true);
        tenant().then((tenant) => (this.tenant = tenant));
    }

    render(): TemplateResult {
        return html` <ak-router-outlet
            .routes=${ROUTES}
            role="main"
            tabindex="-1"
            defaultUrl="/library"
        >
        </ak-router-outlet>`;
    }
}
