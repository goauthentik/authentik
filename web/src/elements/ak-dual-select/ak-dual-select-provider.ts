import { AkControlElement } from "@goauthentik/elements/AkControlElement.js";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter.js";

import { msg } from "@lit/localize";
import { PropertyValues, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import type { Pagination } from "@goauthentik/api";

import "./ak-dual-select.js";
import { AkDualSelect } from "./ak-dual-select.js";
import { type DataProvider, DualSelectEventType, type DualSelectPair } from "./types.js";

/**
 * @element ak-dual-select-provider
 *
 * A top-level component that understands how the authentik pagination interface works,
 * and can provide new pages based upon navigation requests.  This is the interface
 * between authentik and the generic ak-dual-select component; aside from knowing that
 * the Pagination object "looks like Django," the interior components don't know anything
 * about authentik at all and could be dropped into Gravity unchanged.)
 */
@customElement("ak-dual-select-provider")
export class AkDualSelectProvider extends CustomListenerElement(AkControlElement) {
    //#region Properties

    /**
     * A function that takes a page and returns the {@linkcode DualSelectPair DualSelectPair[]}
     * collection with which to update the "Available" pane.
     *
     * @attr
     */
    @property({ type: Object })
    public provider!: DataProvider;

    /**
     * The list of selected items. This is the *complete* list, not paginated, as presented by a
     * component with a multi-select list of items to track.
     *
     * @attr
     */
    @property({ type: Array })
    public selected: DualSelectPair[] = [];

    /**
     * The label for the left ("available") pane
     *
     * @attr
     */
    @property({ attribute: "available-label" })
    public availableLabel = msg("Available options");

    /**
     * The label for the right ("selected") pane
     *
     * @attr
     */
    @property({ attribute: "selected-label" })
    public selectedLabel = msg("Selected options");

    /**
     * The debounce for the search as the user is typing in a request
     *
     * @attr
     */
    @property({ attribute: "search-delay", type: Number })
    public searchDelay = 250;

    public get value() {
        return this.dualSelector.value!.selected.map(([k, _]) => k);
    }

    public json() {
        return this.value;
    }

    //#endregion

    //#region State

    @state()
    protected options: DualSelectPair[] = [];

    #loading = false;

    #didFirstUpdate = false;
    #selected: DualSelectPair[] = [];

    #previousSearchValue = "";

    protected pagination?: Pagination;

    //#endregion

    //#region Refs

    protected dualSelector = createRef<AkDualSelect>();

    //#endregion

    //#region Lifecycle

    public connectedCallback(): void {
        super.connectedCallback();
        this.addCustomListener(DualSelectEventType.NavigateTo, this.#navigationListener);
        this.addCustomListener(DualSelectEventType.Change, this.#changeListener);
        this.addCustomListener(DualSelectEventType.Search, this.#searchListener);

        this.#fetch(1);
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("selected") && !this.#didFirstUpdate) {
            this.#didFirstUpdate = true;
            this.#selected = this.selected;
        }

        if (changedProperties.has("provider")) {
            this.pagination = undefined;
            this.#previousSearchValue = "";
            this.#fetch();
        }
    }

    //#endregion

    //#region Private Methods

    #fetch = async (page?: number, search = this.#previousSearchValue): Promise<void> => {
        if (this.#loading) return;

        this.#previousSearchValue = search;
        this.#loading = true;

        page ??= this.pagination?.current ?? 1;

        return this.provider(page, search)
            .then((data) => {
                this.pagination = data.pagination;
                this.options = data.options;
            })
            .catch((error) => {
                console.error(error);
            })
            .finally(() => {
                this.#loading = false;
            });
    };

    //#endregion

    //#region Event Listeners

    #navigationListener = (event: CustomEvent<number>) => {
        this.#fetch(event.detail, this.#previousSearchValue);
    };

    #changeListener = (event: CustomEvent<{ value: DualSelectPair[] }>) => {
        this.#selected = event.detail.value;
        this.selected = this.#selected;
    };

    #searchListener = (event: CustomEvent<string>) => {
        this.#doSearch(event.detail);
    };

    #searchTimeoutID?: ReturnType<typeof setTimeout>;

    #doSearch = (search: string) => {
        clearTimeout(this.#searchTimeoutID);

        setTimeout(() => {
            this.pagination = undefined;
            this.#fetch(undefined, search);
        }, this.searchDelay);
    };

    //#endregion

    render() {
        return html`<ak-dual-select
            ${ref(this.dualSelector)}
            .options=${this.options}
            .pages=${this.pagination}
            .selected=${this.#selected}
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
