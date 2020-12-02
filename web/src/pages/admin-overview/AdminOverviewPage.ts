import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { AdminOverview } from "../../api/admin_overview";
import { DefaultClient } from "../../api/client";
import { User } from "../../api/user";
import { COMMON_STYLES } from "../../common/styles";
import { AggregatePromiseCard } from "../../elements/cards/AggregatePromiseCard";
import { SpinnerSize } from "../../elements/Spinner";

import "../../elements/AdminLoginsChart";
import "./TopApplicationsTable";

@customElement("ak-admin-status-card")
export class AdminStatusCard extends AggregatePromiseCard {

    @property({type: Number})
    value?: number;

    @property()
    warningText?: string;

    @property({type: Number})
    lessThanThreshold?: number;

    renderNone(): TemplateResult {
        return html`<ak-spinner size=${SpinnerSize.Large}></ak-spinner>`;
    }

    renderGood(): TemplateResult {
        return html`<p class="pb-aggregate-card">
            <i class="fa fa-check-circle"></i> ${this.value}
        </p>`;
    }

    renderBad(): TemplateResult {
        return html`<p class="pb-aggregate-card">
            <i class="fa fa-exclamation-triangle"></i> ${this.value}
        </p>
        <p class="subtext">${this.warningText ? gettext(this.warningText) : ""}</p>`;
    }

    renderInner(): TemplateResult {
        if (!this.value) {
            return this.renderNone();
        }

        return html``;
    }

}

@customElement("ak-admin-overview")
export class AdminOverviewPage extends LitElement {
    @property({attribute: false})
    data?: AdminOverview;

    @property({attribute: false})
    users?: Promise<number>;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    firstUpdated(): void {
        AdminOverview.get().then(value => this.data = value);
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
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-server" header="Workers">

                </ak-aggregate-card>
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-plugged" header="Providers" headerLink="#/administration/providers/">
                    ${this.data ?
        this.data?.providers_without_application > 1 ?
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> 0
                                </p>
                                <p class="subtext">${gettext("At least one Provider has no application assigned.")}</p>` :
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> 0
                                </p>`
        : html`<ak-spinner size=${SpinnerSize.Large}></ak-spinner>`}
                </ak-aggregate-card>
                <ak-aggregate-card class="pf-l-gallery__item pf-m-4-col" icon="pf-icon pf-icon-plugged" header="Policies" headerLink="#/administration/policies/">
                    ${this.data ?
        this.data?.policies_without_binding > 1 ?
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> 0
                                </p>
                                <p class="subtext">${gettext("Policies without binding exist.")}</p>` :
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> 0
                                </p>`
        : html`<ak-spinner size=${SpinnerSize.Large}></ak-spinner>`}
                </ak-aggregate-card>
                <ak-aggregate-card-promise
                    icon="pf-icon pf-icon-user"
                    header="Users"
                    headerLink="#/administration/users/"
                    .promise=${this.users}>
                </ak-aggregate-card-promise>
            </div>
        </section>`;
    }

}
