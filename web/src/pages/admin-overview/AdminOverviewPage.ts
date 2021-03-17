import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";

import "../../elements/charts/AdminLoginsChart";
import "../../elements/cards/AggregatePromiseCard";
import "./TopApplicationsTable";
import "./cards/AdminStatusCard";
import "./cards/FlowCacheStatusCard";
import "./cards/PolicyCacheStatusCard";
import "./cards/PolicyUnboundStatusCard";
import "./cards/ProviderStatusCard";
import "./cards/UserCountStatusCard";
import "./cards/VersionStatusCard";
import "./cards/WorkerStatusCard";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

@customElement("ak-admin-overview")
export class AdminOverviewPage extends LitElement {

    static get styles(): CSSResult[] {
        return [PFGallery, PFPage, PFContent];
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
                    <ak-charts-admin-login></ak-charts-admin-login>
                </ak-aggregate-card>
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Apps with most usage" style="grid-column-end: span 2;grid-row-end: span 3;">
                    <ak-top-applications-table></ak-top-applications-table>
                </ak-aggregate-card>
                <ak-admin-status-card-provider class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-plugged" header="Providers" headerLink="#/core/providers/">
                </ak-admin-status-card-provider>
                <ak-admin-status-card-policy-unbound class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-infrastructure" header="Policies" headerLink="#/policy/policies">
                </ak-admin-status-card-policy-unbound>
                <ak-admin-status-card-user-count class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-user" header="Users" headerLink="#/identity/users">
                </ak-admin-status-card-user-count>
                <ak-admin-status-version class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-bundle" header="Version" headerLink="https://github.com/BeryJu/authentik/releases">
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
