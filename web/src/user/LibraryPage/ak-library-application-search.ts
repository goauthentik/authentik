import Styles from "./ak-library-application-search.css";
import {
    LibraryPageSearchEmpty,
    LibraryPageSearchReset,
    LibraryPageSearchSelected,
    LibraryPageSearchUpdated,
} from "./events.js";

import { AKElement } from "#elements/Base";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";

import type { Application } from "@goauthentik/api";

import Fuse, { FuseResult } from "fuse.js";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

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
        // ---
        PFBase,
        PFDisplay,
        PFFormControl,
        Styles,
    ];

    @property({ attribute: false })
    set apps(value: Application[]) {
        this.fuse.setCollection(value);
    }

    @state()
    protected query = getURLParam<string | null>("q", "");

    protected searchInput = createRef<HTMLInputElement>();

    protected fuse = new Fuse<Application>([], {
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

    public override connectedCallback() {
        super.connectedCallback();

        if (this.query) {
            const matchingApps = this.fuse.search(this.query);

            if (matchingApps.length) {
                this.#dispatchSelected(matchingApps);
            }
        }
    }

    public reset(): void {
        const searchInput = this.searchInput.value;

        if (searchInput) {
            searchInput.value = "";
        }

        this.query = "";

        updateURLParams({
            q: this.query,
        });

        this.dispatchEvent(new LibraryPageSearchReset());
    }

    #dispatchSelected = (apps: FuseResult<Application>[]) => {
        this.dispatchEvent(new LibraryPageSearchUpdated(apps.map((app) => app.item)));
    };

    #inputListener = (event: InputEvent) => {
        this.query = (event.target as HTMLInputElement).value;

        if (!this.query) {
            return this.reset();
        }

        updateURLParams({
            q: this.query,
        });

        const apps = this.fuse.search(this.query);

        if (!apps.length) {
            this.dispatchEvent(new LibraryPageSearchEmpty());
            return;
        }

        this.#dispatchSelected(apps);
    };

    #keyDownListener = (event: KeyboardEvent) => {
        switch (event.key) {
            case "Escape": {
                event.preventDefault();
                this.reset();
                return;
            }
            case "Enter": {
                event.preventDefault();
                this.dispatchEvent(new LibraryPageSearchSelected());
                return;
            }
        }
    };

    render() {
        return html`<input
            ${ref(this.searchInput)}
            name="application-search"
            @input=${this.#inputListener}
            @keydown=${this.#keyDownListener}
            type="search"
            class="pf-c-form-control pf-u-display-none pf-u-display-block-on-md"
            autofocus
            aria-label=${msg("Application search")}
            placeholder=${msg("Search for an application by name...")}
            value=${ifPresent(this.query)}
        />`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-list-search": LibraryPageApplicationSearch;
    }
}
