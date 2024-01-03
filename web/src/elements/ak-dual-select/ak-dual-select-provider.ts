import { AKElement } from "@goauthentik/elements/Base";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

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
    // A function that takes a page and returns the DualSelectPair[] collection with which to update
    // the "Available" pane.
    @property({ type: Object })
    provider!: DataProvider;

    @property({ type: Array })
    selected: DualSelectPair[] = [];

    @property({ attribute: "available-label" })
    availableLabel = "Available options";

    @property({ attribute: "selected-label" })
    selectedLabel = "Selected options";

    @state()
    private options: DualSelectPair[] = [];

    private dualSelector: Ref<AkDualSelect> = createRef();

    private isLoading = false;

    private pagination?: Pagination;

    get value() {
        return this.dualSelector.value!.selected.map(([k, _]) => k);
    }

    selectedMap: WeakMap<DataProvider, DualSelectPair[]> = new WeakMap();

    constructor() {
        super();
        setTimeout(() => this.fetch(1), 0);
        this.onNav = this.onNav.bind(this);
        this.onChange = this.onChange.bind(this);
        // Notify AkForElementHorizontal how to handle this thing.
        this.dataset.akControl = "true";
        this.addCustomListener("ak-pagination-nav-to", this.onNav);
        this.addCustomListener("ak-dual-select-change", this.onChange);
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

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("provider")) {
            this.pagination = undefined;
            if (changedProperties.get("provider")) {
                this.selectedMap.set(changedProperties.get("provider"), this.selected);
                this.selected = this.selectedMap.get(this.provider) ?? [];
            }
            this.fetch();
        }
    }

    async fetch(page?: number) {
        if (this.isLoading) {
            return;
        }
        this.isLoading = true;
        const goto = page ?? this.pagination?.current ?? 1;
        const data = await this.provider(goto);
        this.pagination = data.pagination;
        this.options = data.options;
        this.isLoading = false;
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
