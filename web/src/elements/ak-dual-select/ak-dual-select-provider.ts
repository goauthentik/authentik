import { AkControlElement } from "@goauthentik/elements/AkControlElement.js";
import { debounce } from "@goauthentik/elements/utils/debounce";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { PropertyValues, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import type { Ref } from "lit/directives/ref.js";

import type { Pagination } from "@goauthentik/api";

import "./ak-dual-select";
import { AkDualSelect } from "./ak-dual-select";
import type { DataProvider, DualSelectPair } from "./types";

/**
 * @element ak-dual-select-provider
 *
 * A top-level component that understands how the authentik pagination interface works,
 * and can provide new pages based upon navigation requests.  This is the interface
 * between authentik and the generic ak-dual-select component; aside from knowing that
 * the Pagination object "looks like Django," the interior components don't know anything
 * about authentik at all and could be dropped into Gravity unchanged.)
 *
 */

@customElement("ak-dual-select-provider")
export class AkDualSelectProvider extends CustomListenerElement(AkControlElement) {
    /** A function that takes a page and returns the DualSelectPair[] collection with which to update
     * the "Available" pane.
     *
     * @attr
     */
    @property({ type: Object })
    provider!: DataProvider;

    /**
     * The list of selected items. This is the *complete* list, not paginated, as presented by a
     * component with a multi-select list of items to track.
     *
     * @attr
     */
    @property({ type: Array })
    selected: DualSelectPair[] = [];

    /**
     * The label for the left ("available") pane
     *
     * @attr
     */
    @property({ attribute: "available-label" })
    availableLabel = msg("Available options");

    /**
     * The label for the right ("selected") pane
     *
     * @attr
     */
    @property({ attribute: "selected-label" })
    selectedLabel = msg("Selected options");

    /**
     * The debounce for the search as the user is typing in a request
     *
     * @attr
     */
    @property({ attribute: "search-delay", type: Number })
    searchDelay = 250;

    @state()
    options: DualSelectPair[] = [];

    protected dualSelector: Ref<AkDualSelect> = createRef();

    protected isLoading = false;

    private doneFirstUpdate = false;
    private internalSelected: DualSelectPair[] = [];

    protected pagination?: Pagination;

    constructor() {
        super();
        setTimeout(() => this.fetch(1), 0);
        this.onNav = this.onNav.bind(this);
        this.onChange = this.onChange.bind(this);
        this.onSearch = this.onSearch.bind(this);
        this.addCustomListener("ak-pagination-nav-to", this.onNav);
        this.addCustomListener("ak-dual-select-change", this.onChange);
        this.addCustomListener("ak-dual-select-search", this.onSearch);
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("selected") && !this.doneFirstUpdate) {
            this.doneFirstUpdate = true;
            this.internalSelected = this.selected;
        }

        if (changedProperties.has("searchDelay")) {
            this.doSearch = debounce(
                AkDualSelectProvider.prototype.doSearch.bind(this),
                this.searchDelay,
            );
        }

        if (changedProperties.has("provider")) {
            this.pagination = undefined;
            this.fetch();
        }
    }

    async fetch(page?: number, search = "") {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        const goto = page ?? this.pagination?.current ?? 1;
        const data = await this.provider(goto, search);
        this.pagination = data.pagination;
        this.options = data.options;
        this.isLoading = false;
    }

    onNav(event: Event) {
        if (!(event instanceof CustomEvent)) {
            throw new Error(`Expecting a CustomEvent for navigation, received ${event} instead`);
        }
        this.fetch(event.detail);
    }

    onChange(event: Event) {
        if (!(event instanceof CustomEvent)) {
            throw new Error(`Expecting a CustomEvent for change, received ${event} instead`);
        }
        this.internalSelected = event.detail.value;
        this.selected = this.internalSelected;
    }

    onSearch(event: Event) {
        if (!(event instanceof CustomEvent)) {
            throw new Error(`Expecting a CustomEvent for change, received ${event} instead`);
        }
        this.doSearch(event.detail);
    }

    doSearch(search: string) {
        this.pagination = undefined;
        this.fetch(undefined, search);
    }

    get value() {
        return this.dualSelector.value!.selected.map(([k, _]) => k);
    }

    json() {
        return this.value;
    }

    render() {
        return html`<ak-dual-select
            ${ref(this.dualSelector)}
            .options=${this.options}
            .pages=${this.pagination}
            .selected=${this.internalSelected}
            available-label=${this.availableLabel}
            selected-label=${this.selectedLabel}
        ></ak-dual-select>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select-provider": AkDualSelectProvider;
    }
}
