import { t } from "@lingui/macro";
import { customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Application, CoreApi } from "@goauthentik/api";
import { AKResponse } from "../api/Client";
import { DEFAULT_CONFIG } from "../api/Config";
import { loading } from "../utils";

@customElement("ak-library")
export class LibraryPage extends LitElement {
    @property({ attribute: false })
    apps?: AKResponse<Application>;

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
        return html``;
    }

    render(): TemplateResult {
        return html`${loading(
            this.apps,
            html`${(this.apps?.results.length || 0) > 0
                ? this.renderApps()
                : this.renderEmptyState()}`,
        )}`;
    }
}
