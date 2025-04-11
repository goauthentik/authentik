import { BrandConfig } from "@goauthentik/common/global";
import { Interface } from "@goauthentik/elements/Interface";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { UiThemeEnum } from "@goauthentik/api";

@customElement("ak-loading")
export class Loading extends Interface {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFSpinner,
            PFEmptyState,
            css`
                :host([theme="dark"]) h1 {
                    color: var(--ak-dark-foreground);
                }
            `,
        ];
    }

    _initContexts(): void {
        // Stub function to avoid making API requests for things we don't need. The `Interface` base class loads
        // a bunch of data that is used globally by various things, however this is an interface that is shown
        // very briefly and we don't need any of that data.
    }

    async _initCustomCSS(): Promise<void> {
        // Stub function to avoid fetching custom CSS.
    }

    async getTheme(): Promise<UiThemeEnum> {
        return BrandConfig.uiTheme || UiThemeEnum.Automatic;
    }

    render(): TemplateResult {
        return html` <section
            class="ak-static-page pf-c-page__main-section pf-m-no-padding-mobile pf-m-xl"
        >
            <div class="pf-c-empty-state" style="height: 100vh;">
                <div class="pf-c-empty-state__content">
                    <span
                        class="pf-c-spinner pf-m-xl"
                        role="progressbar"
                        aria-valuetext="${msg("Loading...")}"
                    >
                        <span class="pf-c-spinner__clipper"></span>
                        <span class="pf-c-spinner__lead-ball"></span>
                        <span class="pf-c-spinner__tail-ball"></span>
                    </span>
                    <h1 class="pf-c-title pf-m-lg">${msg("Loading...")}</h1>
                </div>
            </div>
        </section>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-loading": Loading;
    }
}
