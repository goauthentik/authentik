import { AKElement } from "@goauthentik/elements/Base";
import {
    CustomEmitterElement,
    CustomListenerElement,
} from "@goauthentik/elements/utils/eventEmitter";
import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { PropertyValues, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import type { Ref } from "lit/directives/ref.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import { globalVariables, mainStyles } from "./components/styles.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./components/ak-dual-select-available-pane.js";
import { AkDualSelectAvailablePane } from "./components/ak-dual-select-available-pane.js";
import "./components/ak-dual-select-controls.js";
import "./components/ak-dual-select-selected-pane.js";
import { AkDualSelectSelectedPane } from "./components/ak-dual-select-selected-pane.js";
import "./components/ak-pagination.js";
import "./components/ak-search-bar.js";
import {
    BasePagination,
    DualSelectEventType,
    DualSelectPair,
    SearchbarEventDetail,
    SearchbarEventSource,
} from "./types.js";

function localeComparator(a: DualSelectPair, b: DualSelectPair) {
    const aSortBy = a[2];
    const bSortBy = b[2];

    return aSortBy.localeCompare(bSortBy);
}

function keyfinder(key: string) {
    return ([k]: DualSelectPair) => k === key;
}

const DelegatedEvents = [
    DualSelectEventType.AddSelected,
    DualSelectEventType.RemoveSelected,
    DualSelectEventType.AddAll,
    DualSelectEventType.RemoveAll,
    DualSelectEventType.DeleteAll,
    DualSelectEventType.AddOne,
    DualSelectEventType.RemoveOne,
] as const satisfies DualSelectEventType[];

/**
 * @element ak-dual-select
 *
 * A master (but independent) component that shows two lists-- one of "available options" and one of
 * "selected options".  The Available Options panel supports pagination if it receives a valid and
 * active pagination object (based on Django's pagination object) from the invoking component.
 *
 * @fires ak-dual-select-change - A custom change event with the current `selected` list.
 */
@customElement("ak-dual-select")
export class AkDualSelect extends CustomEmitterElement(CustomListenerElement(AKElement)) {
    static styles = [PFBase, PFButton, globalVariables, mainStyles];

    //#region Properties

    /**
     * The list of options to *currently* show.
     *
     * Note that this is not *all* the options,
     * only the currently shown list of options from a pagination collection.
     */
    @property({ type: Array })
    options: DualSelectPair[] = [];

    /**
     * The list of options selected.
     * This is the *entire* list and will not be paginated.
     */
    @property({ type: Array })
    selected: DualSelectPair[] = [];

    @property({ type: Object })
    pages?: BasePagination;

    @property({ attribute: "available-label" })
    availableLabel = msg("Available options");

    @property({ attribute: "selected-label" })
    selectedLabel = msg("Selected options");

    //#endregion

    //#region State

    @state()
    protected selectedFilter: string = "";

    #selectedKeys: Set<string> = new Set();

    //#endregion

    //#region Refs

    availablePane: Ref<AkDualSelectAvailablePane> = createRef();

    selectedPane: Ref<AkDualSelectSelectedPane> = createRef();

    //#endregion

    //#region Lifecycle

    constructor() {
        super();

        for (const eventName of DelegatedEvents) {
            this.addCustomListener(eventName, this.#moveListener);
        }

        this.addCustomListener("ak-dual-select-move", () => {
            this.requestUpdate();
        });

        this.addCustomListener("ak-search", this.#searchListener);
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("selected")) {
            this.#selectedKeys = new Set(this.selected.map(([key]) => key));
        }

        // Pagination invalidates available moveables.
        if (changedProperties.has("options") && this.availablePane.value) {
            this.availablePane.value.clearMove();
        }
    }

    //#endregion

    //#region Event Listeners

    #moveListener = (event: CustomEvent<string>) => {
        match(event.type)
            .with(DualSelectEventType.AddSelected, () => this.addSelected())
            .with(DualSelectEventType.RemoveSelected, () => this.removeSelected())
            .with(DualSelectEventType.AddAll, () => this.addAllVisible())
            .with(DualSelectEventType.RemoveAll, () => this.removeAllVisible())
            .with(DualSelectEventType.DeleteAll, () => this.removeAll())
            .with(DualSelectEventType.AddOne, () => this.addOne(event.detail))
            .with(DualSelectEventType.RemoveOne, () => this.removeOne(event.detail))
            .otherwise(() => {
                throw new Error(`Expected move event here, got ${event.type}`);
            });

        this.dispatchCustomEvent(DualSelectEventType.Change, { value: this.value });

        event.stopPropagation();
    };

    protected addSelected() {
        if (this.availablePane.value!.moveable.length === 0) return;

        this.selected = this.availablePane.value!.moveable.reduce(
            (acc, key) => {
                const value = this.options.find(keyfinder(key));

                return value && !acc.find(keyfinder(value[0])) ? [...acc, value] : acc;
            },
            [...this.selected],
        );

        // This is where the information gets... lossy.  Dammit.
        this.availablePane.value!.clearMove();
    }

    protected addOne(key: string) {
        const requested = this.options.find(keyfinder(key));

        if (!requested) return;
        if (this.selected.find(keyfinder(requested[0]))) return;

        this.selected = [...this.selected, requested];
    }

    // These are the *currently visible* options; the parent node is responsible for paginating and
    // updating the list of currently visible options;
    protected addAllVisible() {
        // Create a new array of all current options and selected, and de-dupe.
        const selected = new Map<string, DualSelectPair>([
            ...this.options.map((pair) => [pair[0], pair] as const),
            ...this.selected.map((pair) => [pair[0], pair] as const),
        ]);

        this.selected = Array.from(selected.values());

        this.availablePane.value!.clearMove();
    }

    protected removeSelected() {
        if (this.selectedPane.value!.moveable.length === 0) return;

        const deselected = new Set(this.selectedPane.value!.moveable);

        this.selected = this.selected.filter(([key]) => !deselected.has(key));

        this.selectedPane.value!.clearMove();
    }

    protected removeOne(key: string) {
        this.selected = this.selected.filter(([k]) => k !== key);
    }

    protected removeAllVisible() {
        // Remove all the items from selected that are in the *currently visible* options list
        const options = new Set(this.options.map(([k]) => k));

        this.selected = this.selected.filter(([k]) => !options.has(k));

        this.selectedPane.value!.clearMove();
    }

    removeAll() {
        this.selected = [];
        this.selectedPane.value!.clearMove();
    }

    #searchListener = (event: CustomEvent<SearchbarEventDetail>) => {
        const { source, value } = event.detail;

        match(source)
            .with(SearchbarEventSource.Available, () => {
                this.dispatchCustomEvent(DualSelectEventType.Search, value);
            })
            .with(SearchbarEventSource.Selected, () => {
                this.selectedFilter = value;
                this.selectedPane.value!.clearMove();
            })
            .exhaustive();

        event.stopPropagation();
    };

    //#endregion

    //#region Public Getters

    get value() {
        return this.selected;
    }

    get canAddAll() {
        // False unless any visible option cannot be found in the selected list, so can still be
        // added.
        const allMoved =
            this.options.length ===
            this.options.filter(([key, _]) => this.#selectedKeys.has(key)).length;

        return this.options.length > 0 && !allMoved;
    }

    get canRemoveAll() {
        // False if no visible option can be found in the selected list
        return (
            this.options.length > 0 &&
            !!this.options.find(([key, _]) => this.#selectedKeys.has(key))
        );
    }

    get needPagination() {
        return (this.pages?.next ?? 0) > 0 || (this.pages?.previous ?? 0) > 0;
    }

    //#endregion

    //#region Render

    render() {
        const selected =
            this.selectedFilter === ""
                ? this.selected
                : this.selected.filter(([_k, v, s]) => {
                      const value = s !== undefined ? s : v;
                      if (typeof value !== "string") {
                          throw new Error("Filter only works when there's a string comparator");
                      }
                      return value.toLowerCase().includes(this.selectedFilter.toLowerCase());
                  });

        const availableCount = this.availablePane.value?.toMove.size ?? 0;
        const selectedCount = this.selectedPane.value?.toMove.size ?? 0;
        const selectedTotal = selected.length;

        const availableStatus =
            availableCount > 0 ? msg(str`${availableCount} item(s) marked to add.`) : "&nbsp;";

        const selectedTotalStatus = msg(str`${selectedTotal} item(s) selected.`);

        const selectedCountStatus =
            selectedCount > 0 ? "  " + msg(str`${selectedCount} item(s) marked to remove.`) : "";

        const selectedStatus = `${selectedTotalStatus} ${selectedCountStatus}`;

        return html`
            <div class="ak-dual-list-selector">
                <div class="ak-available-pane">
                    <div class="pf-c-dual-list-selector__header">
                        <div class="pf-c-dual-list-selector__title">
                            <div class="pf-c-dual-list-selector__title-text">
                                ${this.availableLabel}
                            </div>
                        </div>
                    </div>
                    <ak-search-bar name="ak-dual-list-available-search"></ak-search-bar>
                    <div class="pf-c-dual-list-selector__status">
                        <span
                            class="pf-c-dual-list-selector__status-text"
                            id="basic-available-status-text"
                            >${unsafeHTML(availableStatus)}</span
                        >
                    </div>
                    <ak-dual-select-available-pane
                        ${ref(this.availablePane)}
                        .options=${this.options}
                        .selected=${this.#selectedKeys}
                    ></ak-dual-select-available-pane>
                    ${this.needPagination
                        ? html`<ak-pagination .pages=${this.pages}></ak-pagination>`
                        : nothing}
                </div>
                <ak-dual-select-controls
                    ?add-active=${(this.availablePane.value?.moveable.length ?? 0) > 0}
                    ?remove-active=${(this.selectedPane.value?.moveable.length ?? 0) > 0}
                    ?add-all-active=${this.canAddAll}
                    ?remove-all-active=${this.canRemoveAll}
                    ?delete-all-active=${this.selected.length !== 0}
                    enable-select-all
                    enable-delete-all
                ></ak-dual-select-controls>
                <div class="ak-selected-pane">
                    <div class="pf-c-dual-list-selector__header">
                        <div class="pf-c-dual-list-selector__title">
                            <div class="pf-c-dual-list-selector__title-text">
                                ${this.selectedLabel}
                            </div>
                        </div>
                    </div>
                    <ak-search-bar name="ak-dual-list-selected-search"></ak-search-bar>
                    <div class="pf-c-dual-list-selector__status">
                        <span
                            class="pf-c-dual-list-selector__status-text"
                            id="basic-available-status-text"
                            >${unsafeHTML(selectedStatus)}</span
                        >
                    </div>

                    <ak-dual-select-selected-pane
                        ${ref(this.selectedPane)}
                        .selected=${selected.toSorted(localeComparator)}
                    ></ak-dual-select-selected-pane>
                </div>
            </div>
        `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-dual-select": AkDualSelect;
    }
}
