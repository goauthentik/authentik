import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { AdminOverview } from "../api/admin_overview";
import { DefaultClient } from "../api/client";
import { User } from "../api/user";
import { COMMON_STYLES } from "../common/styles";

@customElement("pb-aggregate-card")
export class AggregateCard extends LitElement {
    @property()
    icon?: string;

    @property()
    header?: string;

    @property()
    headerLink?: string;

    static get styles() {
        return COMMON_STYLES;
    }

    renderInner(): TemplateResult {
        return html`<slot></slot>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col" >
            <div class="pf-c-card__header pf-l-flex pf-m-justify-content-space-between">
                <div class="pf-c-card__header-main">
                    <i class="${this.icon}"></i> ${this.header ? gettext(this.header) : ""}
                </div>
                ${this.headerLink ? html`<a href="${this.headerLink}">
                    <i class="fa fa-external-link-alt"> </i>
                </a>` : ""}
            </div>
            <div class="pf-c-card__body">
                ${this.renderInner()}
            </div>
        </div>`;
    }

}

@customElement("pb-aggregate-card-promise")
export class AggregatePromiseCard extends AggregateCard {
    @property()
    promise?: Promise<string>;

    renderInner(): TemplateResult {
        return html`<p class="pb-aggregate-card">
            ${until(this.promise, html`<pb-spinner></pb-spinner>`)}
        </p>`;
    }

}

@customElement("pb-admin-overview")
export class AdminOverviewPage extends LitElement {
    @property()
    data?: AdminOverview;

    static get styles() {
        return COMMON_STYLES;
    }

    firstUpdated(): void {
        AdminOverview.get().then(value => this.data = value);
    }

    render(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1>${gettext("System Overview")}</h1>
            </div>
        </section>
        <section class="pf-c-page__main-section">
            <div class="pf-l-gallery pf-m-gutter">
                <pb-aggregate-card icon="pf-icon pf-icon-server" header="Logins over the last 24 hours" style="grid-column-end: span 3;grid-row-end: span 2;">
                    <pb-admin-logins-chart url="${DefaultClient.makeUrl(["admin", "metrics"])}"></pb-admin-logins-chart>
                </pb-aggregate-card>
                <pb-aggregate-card icon="pf-icon pf-icon-server" header="Workers">
                    ${this.data ?
        this.data?.worker_count < 1 ?
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> ${this.data.worker_count}
                                </p>
                                <p>${gettext("No workers connected.")}</p>` :
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> ${this.data.worker_count}
                                </p>`
        : html`<pb-spinner></pb-spinner>`}
                </pb-aggregate-card>
                <pb-aggregate-card icon="pf-icon pf-icon-plugged" header="Providers" headerLink="#/administration/providers/">
                    ${this.data ?
        this.data?.providers_without_application < 1 ?
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> 0
                                </p>
                                <p>${gettext("At least one Provider has no application assigned.")}</p>` :
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> 0
                                </p>`
        : html`<pb-spinner></pb-spinner>`}
                </pb-aggregate-card>
                <pb-aggregate-card icon="pf-icon pf-icon-plugged" header="Policies" headerLink="#/administration/policies/">
                    ${this.data ?
        this.data?.policies_without_binding < 1 ?
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> 0
                                </p>
                                <p>${gettext("Policies without binding exist.")}</p>` :
            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> 0
                                </p>`
        : html`<pb-spinner></pb-spinner>`}
                </pb-aggregate-card>
                <pb-aggregate-card-promise
                    icon="pf-icon pf-icon-user"
                    header="Users"
                    headerLink="#/administration/users/"
                    .promise=${User.count()}>
                </pb-aggregate-card-promise>
            </div>
        </section>`;
    }

}
