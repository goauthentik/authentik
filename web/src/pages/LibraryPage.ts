import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import { Application } from "../api/Applications";
import { AKResponse } from "../api/Client";
import { COMMON_STYLES } from "../common/styles";
import { loading, truncate } from "../utils";

@customElement("ak-library-app")
export class LibraryApplication extends LitElement {
    @property({attribute: false})
    application?: Application;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                a {
                    height: 100%;
                }
                i.pf-icon {
                    height: 36px;
                }
                .pf-c-avatar {
                    --pf-c-avatar--BorderRadius: 0;
                }
            `
        );
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }
        return html` <a href="${this.application.launch_url}" class="pf-c-card pf-m-hoverable pf-m-compact">
            <div class="pf-c-card__header">
                ${this.application.meta_icon
                    ? html`<img class="app-icon pf-c-avatar" src="${ifDefined(this.application.meta_icon)}" alt="Application Icon"/>`
                    : html`<i class="pf-icon pf-icon-arrow"></i>`}
            </div>
            <div class="pf-c-card__title">
                <p id="card-1-check-label">${this.application.name}</p>
                <div class="pf-c-content">
                    <small>${this.application.meta_publisher}</small>
                </div>
            </div>
            <div class="pf-c-card__body">${truncate(this.application.meta_description, 35)}</div>
        </a>`;
    }

}

@customElement("ak-library")
export class LibraryPage extends LitElement {
    @property({attribute: false})
    apps?: AKResponse<Application>;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(css`
            :host,
            main {
                height: 100%;
            }
        `);
    }

    firstUpdated(): void {
        Application.list().then((r) => (this.apps = r));
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
