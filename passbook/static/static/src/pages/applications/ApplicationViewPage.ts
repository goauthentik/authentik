import { css, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application } from "../../api/application";
import { DefaultClient } from "../../api/client";
import { COMMON_STYLES } from "../../common/styles";
import { Table } from "../../elements/Table";

@customElement("pb-bound-policies-list")
export class BoundPoliciesList extends Table {
    @property()
    target?: string;

    apiEndpoint(): string[] {
        return ["policies", "bindings", `?target=${this.target}`];
    }

    columns(): string[] {
        return ["Foo"];
    }

    row(item: any): TemplateResult[] {
        return [html`${item}`];
    }
}

@customElement("pb-application-view")
export class ApplicationViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.applicationSlug = value.slug;
    }

    @property()
    set applicationSlug(value: string) {
        Application.get(value).then((app) => (this.application = app));
    }

    @property()
    application?: Application;

    static get styles() {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
            `
        );
    }

    render() {
        if (!this.application) {
            return html``;
        }
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <img class="pf-icon" src="${this.application?.meta_icon || ""}" />
                        ${this.application?.name}
                    </h1>
                    <p>${this.application?.meta_publisher}</p>
                </div>
            </section>
            <pb-tabs>
                <section
                    slot="page-1"
                    tab-title="Users"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-gallery pf-m-gutter">
                        <div
                            class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col"
                            style="grid-column-end: span 3;grid-row-end: span 2;"
                        >
                            <div class="pf-c-card__header">
                                <div class="pf-c-card__header-main">
                                    <i class="pf-icon pf-icon-server"></i> Logins over the last 24
                                    hours
                                </div>
                            </div>
                            <div class="pf-c-card__body">
                                <pb-admin-logins-chart
                                    url="${DefaultClient.makeUrl(
                                        "core",
                                        "applications",
                                        this.application?.slug!,
                                        "metrics"
                                    )}"
                                ></pb-admin-logins-chart>
                            </div>
                        </div>
                    </div>
                </section>
                <div
                    slot="page-2"
                    tab-title="Policy Bindings"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-gallery pf-m-gutter">
                        <div
                            class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col"
                            style="grid-column-end: span 3;grid-row-end: span 2;"
                        >
                            <pb-bound-policies-list
                                .target=${this.application.pk}
                            ></pb-bound-policies-list>
                        </div>
                    </div>
                </div>
            </pb-tabs>`;
    }
}
