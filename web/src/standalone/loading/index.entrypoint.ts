import { LightInterface } from "@goauthentik/elements/Interface";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-loading")
export class Loading extends LightInterface {
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
