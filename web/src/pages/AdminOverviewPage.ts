import { gettext } from "django";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { AdminOverview } from "../api/admin_overview";
import { DefaultClient } from "../api/client";
import { COMMON_STYLES } from "../common/styles";

@customElement("pb-aggregate-card")
export class AggregateCard extends LitElement {
    @property()
    icon?: string;

    @property()
    header?: string;

    static get styles() {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col" >
            <div class="pf-c-card__header">
                <div class="pf-c-card__header-main">
                    <i class="${this.icon}"></i> ${this.header ? gettext(this.header) : ""}
                </div>
            </div>
            <div class="pf-c-card__body">
                <slot></slot>
            </div>
        </div>`;
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
                        this.data?.worker_count! < 1 ?
                            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-exclamation-triangle"></i> ${this.data.worker_count}
                                </p>
                                <p>${gettext("No workers connected.")}</p>` :
                            html`<p class="pb-aggregate-card">
                                    <i class="fa fa-check-circle"></i> ${this.data.worker_count}
                                </p>`
                    : html`<pb-spinner></pb-spinner>`}
                </pb-aggregate-card>
            </div>
        </section>`;
    }

}
