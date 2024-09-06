import { AKElement } from "@goauthentik/elements/Base.js";

import { TemplateResult, css, html, nothing } from "lit";

import PFToolbar from "@patternfly/patternfly/components/Toolbar/toolbar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export class Toolbar extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFToolbar,
            css`
                .pf-c-toolbar__content {
                    row-gap: var(--pf-global--spacer--sm);
                }
                .pf-c-toolbar__item .pf-c-input-group {
                    padding: 0 var(--pf-global--spacer--sm);
                }
            `,
        ];
    }

    renderSearch() {
        return nothing;
    }

    renderToolbar() {
        return nothing;
    }

    renderToolbarSelected() {
        return nothing;
    }

    renderToolbarAfter() {
        return nothing;
    }

    renderPagination() {
        return nothing;
    }

    renderToolbarContainer(): TemplateResult {
        const [search, toolbar, after, selected, pagination] = [
            this.renderSearch(),
            this.renderToolbar(),
            this.renderToolbarAfter(),
            this.renderToolbarSelected(),
            this.renderPagination(),
        ];

        return html`<div class="pf-c-toolbar">
            <div class="pf-c-toolbar__content">
                ${search !== nothing
                    ? html`<div class="pf-c-toolbar__group pf-m-search-filter">${search}</div>`
                    : nothing}
                ${toolbar !== nothing
                    ? html`<div class="pf-c-toolbar__bulk-select">${toolbar}</div>`
                    : nothing}
                ${after !== nothing
                    ? html`<div class="pf-c-toolbar__group">${after}</div>`
                    : nothing}
                ${selected !== nothing
                    ? html`<div class="pf-c-toolbar__group">${selected}</div>`
                    : nothing}
                ${pagination}
            </div>
        </div>`;
    }
}
