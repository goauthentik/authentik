import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application, CoreApi } from "authentik-api";
import { AKResponse } from "../api/Client";
import { DEFAULT_CONFIG } from "../api/Config";
import { loading } from "../utils";

import "@carbon/ibmdotcom-web-components/es/components/card-section-images/card-section-images";
import "@carbon/ibmdotcom-web-components/es/components/card/card-eyebrow";
import "@carbon/ibmdotcom-web-components/es/components/card/card-heading";
import "@carbon/ibmdotcom-web-components/es/components/card/card-footer";
import "@carbon/ibmdotcom-web-components/es/components/card-group/card-group";
import "@carbon/ibmdotcom-web-components/es/components/card-group/card-group-item";
import "@carbon/ibmdotcom-web-components/es/components/content-block/content-block-heading";

@customElement("ak-library")
export class LibraryPage extends LitElement {

    @property({attribute: false})
    apps?: AKResponse<Application>;

    static get styles(): CSSResult[] {
        return [css`
            dds-card-heading {
                margin-bottom: 2rem;
            }
            dds-card-heading.icon {
                display: flex;
            }
            dds-card-heading img {
                max-height: 48px;
            }
            @media (min-width: 66rem) {
                dds-card-group {
                    grid-template-columns: repeat(6, 1fr);
                }
            }
        `];
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
                <h1 class="pf-c-title pf-m-lg">${t`No Applications available.`}</h1>
                <div class="pf-c-empty-state__body">
                    ${t`Either no applications are defined, or you don't have access to any.`}
                </div>
            </div>
        </div>`;
    }

    renderApps(): TemplateResult {
        return html`
        <dds-card-group>
            ${this.apps?.results.map((app) => html`
            <dds-card-group-item href="${app.launchUrl || ""}">
                <dds-card-heading slot="pictogram" class="icon">
                    <img src="${app.metaIcon ? app.metaIcon : "/static/icons/application.svg"}" alt="app icon" loading="lazy">
                </dds-card-heading>
                <dds-card-heading>${app.name}</dds-card-heading>
                <dds-card-footer slot="footer">
                    ${app.metaPublisher}
                </dds-card-footer>
            </dds-card-group-item>`)}
        </dds-card-group>`;
    }

    render(): TemplateResult {
        return html`<div class="bx--grid">
            <div class="bx--row">
                <div class="bx--offset-lg-2 bx--col-lg-8">
                    <dds-content-block-heading>
                        ${t`My Applications`}
                    </dds-content-block-heading>
                    ${loading(this.apps, html`${(this.apps?.results.length || 0) > 0 ?
                        this.renderApps() :
                        this.renderEmptyState()}`)}
                </div>
            </div>
        </div>`;
    }
}
