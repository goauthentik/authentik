import { AKElement } from "@goauthentik/elements/Base";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import Fuse from "fuse.js";

import { t } from "@lingui/macro";

import { css, html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import type { Application } from "@goauthentik/api";

import { SEARCH_ITEM_SELECTED, SEARCH_UPDATED } from "./constants";
import { customEvent } from "./helpers";

@customElement("ak-library-list-search")
export class LibraryPageApplicationList extends AKElement {
    static styles = [
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
        `,
    ];

    @property()
    apps: Application[] = [];

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
            threshold: 0.5,
        });
    }

    onSelected(apps: Fuse.FuseResult<Application>[]) {
        this.dispatchEvent(
            customEvent(SEARCH_UPDATED, {
                apps: apps.map((app) => app.item),
            }),
        );
    }

    connectedCallback() {
        super.connectedCallback();
        this.fuse.setCollection(this.apps);
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
        this.onSelected([]);
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
        if (apps.length < 1) return;
        this.onSelected(apps);
    }

    onKeyDown(ev: KeyboardEvent) {
        switch (ev.key) {
            case "Escape": {
                this.resetSearch();
                return;
            }
            case "Enter": {
                this.dispatchEvent(customEvent(SEARCH_ITEM_SELECTED));
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
            placeholder=${t`Search...`}
            value=${ifDefined(this.query)}
        />`;
    }
}
