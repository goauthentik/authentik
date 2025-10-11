import {
    LibraryPageSearchEmpty,
    LibraryPageSearchReset,
    LibraryPageSearchSelected,
    LibraryPageSearchUpdated,
} from "./events.js";

import { AKElement } from "#elements/Base";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";

import type { Application } from "@goauthentik/api";

import Fuse, { FuseResult } from "fuse.js";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

/**
 * @element ak-library-list-search
 *
 * @class LibraryPageApplicationSearch
 *
 * @classdesc
 *
 * The interface between our list of applications shown to the user, an input box, and the Fuse
 * fuzzy search library.
 *
 * @fires LibraryPageSearchUpdated
 * @fires LibraryPageSearchEmpty
 * @fires LibraryPageSearchReset
 *
 */
@customElement("ak-library-application-search")
export class LibraryPageApplicationSearch extends AKElement {
    static styles = [
        PFBase,
        PFDisplay,
        PFFormControl,
        css`
            input[name="application-search"] {
                background-color: transparent;
                width: 28ch;
                font-size: var(--pf-global--FontSize--xl);

                border-inline: none;
                border-block-start: none;

                &:focus,
                &:hover {
                    --pf-c-form-control--BorderBottomColor: var(--ak-accent);
                }
            }
        `,
        // HACK: Fixes Lit Analyzer's outdated parser.
        (css as typeof css) /*css*/ `
            input[name="application-search"] {
                @media not (prefers-contrast: more) {
                    outline: none;
                }
            }
        `,
    ];

    @property({ attribute: false })
    set apps(value: Application[]) {
        this.fuse.setCollection(value);
    }

    @property()
    query = getURLParam<string | undefined>("search", undefined);

    @query("input")
    searchInput?: HTMLInputElement;

    fuse: Fuse<Application>;

    constructor() {
        super();
        this.fuse = new Fuse([], {
            keys: [
                { name: "name", weight: 3 },
                "slug",
                "group",
                { name: "metaDescription", weight: 0.5 },
                { name: "metaPublisher", weight: 0.5 },
            ],
            findAllMatches: true,
            includeScore: true,
            shouldSort: true,
            ignoreFieldNorm: true,
            useExtendedSearch: true,
            threshold: 0.3,
        });
    }

    onSelected(apps: FuseResult<Application>[]) {
        this.dispatchEvent(new LibraryPageSearchUpdated(apps.map((app) => app.item)));
    }

    connectedCallback() {
        super.connectedCallback();
        if (!this.query) {
            return;
        }
        const matchingApps = this.fuse.search(this.query);
        if (matchingApps.length < 1) {
            return;
        }
        this.onSelected(matchingApps);
    }

    resetSearch(): void {
        if (this.searchInput) {
            this.searchInput.value = "";
        }
        this.query = "";
        updateURLParams({
            search: this.query,
        });
        this.dispatchEvent(new LibraryPageSearchReset());
    }

    onInput(ev: InputEvent) {
        this.query = (ev.target as HTMLInputElement).value;
        if (this.query === "") {
            return this.resetSearch();
        }
        updateURLParams({
            search: this.query,
        });

        const apps = this.fuse.search(this.query);
        if (apps.length < 1) {
            this.dispatchEvent(new LibraryPageSearchEmpty());
            return;
        }

        this.onSelected(apps);
    }

    onKeyDown(ev: KeyboardEvent) {
        switch (ev.key) {
            case "Escape": {
                this.resetSearch();
                return;
            }
            case "Enter": {
                this.dispatchEvent(new LibraryPageSearchSelected());
                return;
            }
        }
    }

    render() {
        return html`<input
            name="application-search"
            @input=${this.onInput}
            @keydown=${this.onKeyDown}
            type="search"
            class="pf-c-form-control pf-u-display-none pf-u-display-block-on-md"
            autofocus
            aria-label=${msg("Application search")}
            placeholder=${msg("Search for an application by name...")}
            value=${ifDefined(this.query)}
        />`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-list-search": LibraryPageApplicationSearch;
    }
}
