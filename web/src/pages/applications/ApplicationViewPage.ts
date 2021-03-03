import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application } from "../../api/Applications";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/policies/BoundPoliciesList";
import "../../elements/utils/LoadingState";

@customElement("ak-application-view")
export class ApplicationViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.applicationSlug = value.slug;
    }

    @property()
    set applicationSlug(value: string) {
        Application.get(value).then((app) => (this.application = app));
    }

    @property({attribute: false})
    application?: Application;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
                ak-tabs {
                    height: 100%;
                }
            `
        );
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        ${gettext("Loading...")}
                    </h1>
                </div>
            </section>
            <ak-loading-state></ak-loading-state>`;
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
            <ak-tabs>
                <section slot="page-1" data-tab-title="${gettext("Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-4-col" style="grid-column-end: span 3;grid-row-end: span 2;">
                            <div class="pf-c-card__header">
                                <div class="pf-c-card__header-main">
                                    <i class="pf-icon pf-icon-server"></i> ${gettext("Logins over the last 24 hours")}
                                </div>
                            </div>
                            <div class="pf-c-card__body">
                                ${this.application ? html`
                                    <ak-admin-logins-chart
                                        url="${["core", "applications", this.application?.slug, "metrics"]}">
                                    </ak-admin-logins-chart>`: ""}
                            </div>
                        </div>
                        <div class="pf-c-card pf-c-card-aggregate pf-l-gallery__item pf-m-2-col">
                            <div class="pf-c-card__header">
                                <div class="pf-c-card__header-main">
                                    <i class="fas fa-external-link-alt"></i> ${gettext("Related")}
                                </div>
                            </div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    ${this.application.provider ?
                                    html`<div class="pf-c-description-list__group">
                                            <dt class="pf-c-description-list__term">
                                                <span class="pf-c-description-list__text">${gettext("Provider")}</span>
                                            </dt>
                                            <dd class="pf-c-description-list__description">
                                                <div class="pf-c-description-list__text">
                                                    <a href="#/core/providers/${this.application.provider.pk}">
                                                        ${this.application.provider.name}
                                                    </a>
                                                </div>
                                            </dd>
                                        </div>`:
                                    html``}
                                </dl>
                            </div>
                        </div>
                    </div>
                </section>
                <div slot="page-2" data-tab-title="${gettext("Policy Bindings")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__header-main">
                                ${gettext("These policies control which users can access this application.")}
                            </div>
                        </div>
                        <ak-bound-policies-list .target=${this.application.pk}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
