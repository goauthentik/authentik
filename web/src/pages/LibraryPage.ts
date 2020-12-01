import { css, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application } from "../api/application";
import { PBResponse } from "../api/client";
import { COMMON_STYLES } from "../common/styles";
import { truncate } from "../utils";

@customElement("pb-library")
export class ApplicationViewPage extends LitElement {
    @property()
    apps?: PBResponse<Application>;

    static get styles() {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
            `
        );
    }

    firstUpdated(): void {
        Application.list().then((r) => (this.apps = r));
    }

    renderEmptyState(): TemplateResult {
        return html` <div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <i class="fas fa-cubes pf-c-empty-state__icon" aria-hidden="true"></i>
                <h1 class="pf-c-title pf-m-lg">No Applications available.</h1>
                <div class="pf-c-empty-state__body">
                    Either no applications are defined, or you don't have access to any.
                </div>
                {% if perms.passbook_core.add_application %}
                <a
                    href="{% url 'passbook_admin:application-create' %}"
                    class="pf-c-button pf-m-primary"
                    type="button"
                >
                    {% trans 'Create Application' %}
                </a>
                {% endif %}
            </div>
        </div>`;
    }

    renderApp(app: Application): TemplateResult {
        return html` <a href="${app.launch_url}" class="pf-c-card pf-m-hoverable pf-m-compact">
            <div class="pf-c-card__header">
                ${app.meta_icon
        ? html`<img
                          class="app-icon pf-c-avatar"
                          src="${app.meta_icon}"
                          alt="Application Icon"
                      />`
        : html`<i class="pf-icon pf-icon-arrow"></i>`}
            </div>
            <div class="pf-c-card__title">
                <p id="card-1-check-label">${app.name}</p>
                <div class="pf-c-content">
                    <small>${app.meta_publisher}</small>
                </div>
            </div>
            <div class="pf-c-card__body">${truncate(app.meta_description, 35)}</div>
        </a>`;
    }

    renderLoading(): TemplateResult {
        return html`<div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <div class="pf-l-bullseye">
                    <div class="pf-l-bullseye__item">
                        <span
                            class="pf-c-spinner pf-m-xl"
                            role="progressbar"
                            aria-valuetext="Loading..."
                        >
                            <span class="pf-c-spinner__clipper"></span>
                            <span class="pf-c-spinner__lead-ball"></span>
                            <span class="pf-c-spinner__tail-ball"></span>
                        </span>
                    </div>
                </div>
            </div>
        </div>`;
    }

    render(): TemplateResult {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="pf-icon pf-icon-applications"></i>
                        Applications
                    </h1>
                </div>
            </section>
            ${this.apps
        ? html`<section class="pf-c-page__main-section">
                      <div class="pf-l-gallery pf-m-gutter">
                          ${this.apps.results.map((app) => this.renderApp(app))}
                      </div>
                  </section>`
        : this.renderLoading()}
        </main>`;
    }
}
