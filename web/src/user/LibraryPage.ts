import { t } from "@lingui/macro";
import {
    css,
    CSSResult,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
import { Application, CoreApi } from "@goauthentik/api";
import { AKResponse } from "../api/Client";
import { DEFAULT_CONFIG } from "../api/Config";
import { loading } from "../utils";
import AKGlobal from "../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import "./LibraryApplication";

@customElement("ak-library")
export class LibraryPage extends LitElement {
    @property({ attribute: false })
    apps?: AKResponse<Application>;

    constructor() {
        super();
        new CoreApi(DEFAULT_CONFIG).coreApplicationsList({}).then((apps) => {
            this.apps = apps;
        });
    }

    pageTitle(): string {
        return t`My Applications`;
    }

    static get styles(): CSSResult[] {
        return [PFBase, PFEmptyState, PFPage, PFContent, PFGallery, AKGlobal].concat(css`
            :host,
            main {
                height: 100%;
                padding: 3% 5%;
            }
        `);
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
        return html`<div class="pf-l-gallery pf-m-gutter">
            ${this.apps?.results
                .filter((app) => app.launchUrl)
                .map((app) => html`<ak-library-app .application=${app}></ak-library-app>`)}
        </div>`;
    }

    render(): TemplateResult {
        return html`<main role="main" class="pf-c-page__main" tabindex="-1" id="main-content">
            <div class="pf-c-content">
                <h1>${t`My applications`}</h1>
            </div>
            <section class="pf-c-page__main-section">
                ${loading(
                    this.apps,
                    html`${(this.apps?.results.length || 0) > 0
                        ? this.renderApps()
                        : this.renderEmptyState()}`,
                )}
            </section>
        </main>`;
    }
}
