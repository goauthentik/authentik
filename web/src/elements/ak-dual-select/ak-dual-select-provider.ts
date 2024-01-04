import { AKElement } from "@goauthentik/elements/Base";
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
export class AkDualSelectProvider extends CustomListenerElement(AKElement) {
    /** A function that takes a page and returns the DualSelectPair[] collection with which to update
     * the "Available" pane.
     */
    @property({ type: Object })
    provider!: DataProvider;

    @property({ type: Array })
    selected: DualSelectPair[] = [];

    @property({ attribute: "available-label" })
    availableLabel = msg("Available options");

    @property({ attribute: "selected-label" })
    selectedLabel = msg("Selected options");

    /** The remote lists are debounced by definition. This is the interval for the debounce. */
    @property({ attribute: "search-delay", type: Number })
    searchDelay = 250;

    @state()
    private options: DualSelectPair[] = [];

    private dualSelector: Ref<AkDualSelect> = createRef();

    private isLoading = false;

    private pagination?: Pagination;

    selectedMap: WeakMap<DataProvider, DualSelectPair[]> = new WeakMap();

    constructor() {
        super();
        setTimeout(() => this.fetch(1), 0);
        // Notify AkForElementHorizontal how to handle this thing.
        this.dataset.akControl = "true";
        this.onNav = this.onNav.bind(this);
        this.onChange = this.onChange.bind(this);
        this.onSearch = this.onSearch.bind(this);
        this.addCustomListener("ak-pagination-nav-to", this.onNav);
        this.addCustomListener("ak-dual-select-change", this.onChange);
        this.addCustomListener("ak-dual-select-search", this.onSearch);
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("searchDelay")) {
            this.doSearch = debounce(this.doSearch.bind(this), this.searchDelay);
        }

        if (changedProperties.has("provider")) {
            this.pagination = undefined;
            if (changedProperties.get("provider")) {
                this.selectedMap.set(changedProperties.get("provider"), this.selected);
                this.selected = this.selectedMap.get(this.provider) ?? [];
            }
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
        this.selected = event.detail.value;
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

    render() {
        return html`<ak-dual-select
            ${ref(this.dualSelector)}
            .options=${this.options}
            .pages=${this.pagination}
            .selected=${this.selected}
            available-label=${this.availableLabel}
            selected-label=${this.selectedLabel}
        ></ak-dual-select>`;
    }
}
