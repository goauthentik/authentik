import { AKElement } from "@goauthentik/elements/Base";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import Fuse from "fuse.js";
import { FuseResult } from "fuse.js";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import type { Application } from "@goauthentik/api";

import {
    LibraryPageSearchEmpty,
    LibraryPageSearchReset,
    LibraryPageSearchSelected,
    LibraryPageSearchUpdated,
} from "./events.js";

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
    static get styles() {
        return [
            PFBase,
            PFDisplay,
            css`
                input {
                    width: 30ch;
                    box-sizing: border-box;
                    border: 0;
                    border-bottom: 1px solid;
                    border-bottom-color: var(--ak-accent);
                    background-color: transparent;
                    font-size: 1.5rem;
                }

                input:focus {
                    outline: 0;
                }

                @media (prefers-color-scheme: dark) {
                    input {
                        color: var(--ak-dark-foreground) !important;
                    }
                }
            `,
        ];
    }

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
            @input=${this.onInput}
            @keydown=${this.onKeyDown}
            type="text"
            class="pf-u-display-none pf-u-display-block-on-md"
            autofocus
            placeholder=${msg("Search...")}
            value=${ifDefined(this.query)}
        />`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-list-search": LibraryPageApplicationSearch;
    }
}
