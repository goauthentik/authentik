import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { DefaultClient } from "../../api/Client";
import { User } from "../../api/Users";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/AdminLoginsChart";
import "../../elements/cards/AggregatePromiseCard";
import "./TopApplicationsTable";
import "./cards/AdminStatusCard";
import "./cards/FlowCacheStatusCard";
import "./cards/PolicyCacheStatusCard";
import "./cards/PolicyUnboundStatusCard";
import "./cards/ProviderStatusCard";
import "./cards/VersionStatusCard";
import "./cards/WorkerStatusCard";

@customElement("ak-admin-overview")
export class AdminOverviewPage extends LitElement {
    @property({attribute: false})
    users?: Promise<number>;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    firstUpdated(): void {
        this.users = User.count();
    }

    render(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1>${gettext("System Overview")}</h1>
            </div>
        </section>
        <section class="pf-c-page__main-section">
            <div class="pf-l-gallery pf-m-gutter">
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Logins over the last 24 hours" style="grid-column-end: span 3;grid-row-end: span 2;">
                    <ak-admin-logins-chart url="${DefaultClient.makeUrl(["admin", "metrics"])}"></ak-admin-logins-chart>
                </ak-aggregate-card>
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Apps with most usage" style="grid-column-end: span 2;grid-row-end: span 3;">
                    <ak-top-applications-table></ak-top-applications-table>
                </ak-aggregate-card>
                <ak-admin-status-card-provider class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-plugged" header="Providers" headerLink="#/administration/providers/">
                </ak-admin-status-card-provider>
                <ak-admin-status-card-policy-unbound class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-infrastructure" header="Policies" headerLink="#/administration/policies/">
                </ak-admin-status-card-policy-unbound>
                <ak-aggregate-card-promise
                    icon="pf-icon pf-icon-user"
                    header="Users"
                    headerLink="#/administration/users/"
                    .promise=${this.users}>
                </ak-aggregate-card-promise>
                <ak-admin-status-version class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-bundle" header="Version">
                </ak-admin-status-version>
                <ak-admin-status-card-workers class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Workers">
                </ak-admin-status-card-workers>
                <ak-admin-status-card-policy-cache class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Cached Policies">
                </ak-admin-status-card-policy-cache>
                <ak-admin-status-card-flow-cache class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Cached Flows">
                </ak-admin-status-card-flow-cache>
            </div>
        </section>`;
    }

}
