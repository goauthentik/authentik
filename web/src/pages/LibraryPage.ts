import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";
import { Application, CoreApi } from "authentik-api";
import { AKResponse } from "../api/Client";
import { DEFAULT_CONFIG } from "../api/Config";
import { me } from "../api/Users";
import { loading, truncate } from "../utils";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../authentik.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

@customElement("ak-library-app")
export class LibraryApplication extends LitElement {
    @property({attribute: false})
    application?: Application;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFAvatar, AKGlobal,
            css`
                a {
                    height: 100%;
                }
                i.pf-icon {
                    height: 36px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .pf-c-avatar {
                    --pf-c-avatar--BorderRadius: 0;
                }
                .pf-c-card__header {
                    min-height: 60px;
                    justify-content: space-between;
                }
                .pf-c-card__header a {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    margin-right: 0.25em;
                }
            `
        ];
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }
        return html` <a href="${ifDefined(this.application.launchUrl)}" class="pf-c-card pf-m-hoverable pf-m-compact">
            <div class="pf-c-card__header">
                ${this.application.metaIcon
                    ? html`<img class="app-icon pf-c-avatar" src="${ifDefined(this.application.metaIcon)}" alt="Application Icon"/>`
                    : html`<i class="fas fas fa-share-square"></i>`}
                ${until(me().then((u) => {
                    if (!u.user.isSuperuser) return html``;
                    return html`
                        <a href="#/core/applications/${this.application?.slug}">
                            <i class="fas fa-pencil-alt"></i>
                        </a>
                    `;
                }))}
            </div>
            <div class="pf-c-card__title">
                <p id="card-1-check-label">${this.application.name}</p>
                <div class="pf-c-content">
                    <small>${this.application.metaPublisher}</small>
                </div>
            </div>
            <div class="pf-c-card__body">${truncate(this.application.metaDescription, 35)}</div>
        </a>`;
    }

}

@customElement("ak-library")
export class LibraryPage extends LitElement {
    @property({attribute: false})
    apps?: AKResponse<Application>;

    pageTitle(): string {
        return gettext("Applications");
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFEmptyState, PFTitle, PFPage, PFContent, PFGallery, AKGlobal].concat(css`
            :host,
            main {
                height: 100%;
            }
        `);
    }

    firstUpdated(): void {
        new CoreApi(DEFAULT_CONFIG).coreApplicationsList({}).then((apps) => {
            this.apps = apps;
        });
    }

    renderEmptyState(): TemplateResult {
        return html` <div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">${gettext("No Applications available.")}</h1>
                <div class="pf-c-empty-state__body">
                    ${gettext("Either no applications are defined, or you don't have access to any.")}
                </div>
            </div>
        </div>`;
    }

    renderApps(): TemplateResult {
        return html`<div class="pf-l-gallery pf-m-gutter">
            ${this.apps?.results.map((app) => html`<ak-library-app .application=${app}></ak-library-app>`)}
        </div>`;
    }

    render(): TemplateResult {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="pf-icon pf-icon-applications"></i>
                        ${gettext("Applications")}
                    </h1>
                </div>
            </section>
            <section class="pf-c-page__main-section">
            ${loading(this.apps, html`${(this.apps?.results.length || 0) > 0 ?
                this.renderApps() :
                this.renderEmptyState()}`)}
            </section>
        </main>`;
    }
}
