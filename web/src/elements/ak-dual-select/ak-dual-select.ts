import { AKElement } from "@goauthentik/elements/Base";
import {
    CustomEmitterElement,
    CustomListenerElement,
} from "@goauthentik/elements/utils/eventEmitter";

import { msg, str } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";
import type { Ref } from "lit/directives/ref.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDualListSelector from "@patternfly/patternfly/components/DualListSelector/dual-list-selector.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "./components/ak-dual-select-available-pane";
import { AkDualSelectAvailablePane } from "./components/ak-dual-select-available-pane";
import "./components/ak-dual-select-controls";
import "./components/ak-dual-select-selected-pane";
import { AkDualSelectSelectedPane } from "./components/ak-dual-select-selected-pane";
import "./components/ak-pagination";
import { globalVariables, mainStyles } from "./components/styles.css";
import {
    EVENT_ADD_ALL,
    EVENT_ADD_ONE,
    EVENT_ADD_SELECTED,
    EVENT_DELETE_ALL,
    EVENT_REMOVE_ALL,
    EVENT_REMOVE_ONE,
    EVENT_REMOVE_SELECTED,
} from "./constants";
import type { BasePagination, DualSelectPair } from "./types";

const styles = [
    PFBase,
    PFButton,
    globalVariables,
    mainStyles,
    css`
        :host {
            --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min: 12.5rem;
            --pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max: 28.125rem;
        }
        .ak-dual-list-selector {
            display: grid;
            grid-template-columns:
                minmax(
                    var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min),
                    var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max)
                )
                min-content
                minmax(
                    var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--min),
                    var(--pf-c-dual-list-selector--GridTemplateColumns--pane--MinMax--max)
                );
        }
        .ak-available-pane,
        ak-dual-select-controls,
        .ak-selected-pane {
            height: 100%;
        }
    `,
];

@customElement("ak-dual-select")
export class AkDualSelect extends CustomEmitterElement(CustomListenerElement(AKElement)) {
    static get styles() {
        return styles;
    }

    @property({ type: Array })
    options: DualSelectPair[] = [];

    @property({ type: Array })
    selected: DualSelectPair[] = [];

    @property({ type: Object })
    pages?: BasePagination;

    @property({ attribute: "available-label" })
    availableLabel = "Available options";

    @property({ attribute: "selected-label" })
    selectedLabel = "Selected options";

    availablePane: Ref<AkDualSelectAvailablePane> = createRef();

    selectedPane: Ref<AkDualSelectSelectedPane> = createRef();

    constructor() {
        super();
        this.handleMove = this.handleMove.bind(this);
        [
            EVENT_ADD_ALL,
            EVENT_ADD_SELECTED,
            EVENT_DELETE_ALL,
            EVENT_REMOVE_ALL,
            EVENT_REMOVE_SELECTED,
            EVENT_ADD_ONE,
            EVENT_REMOVE_ONE,
        ].forEach((eventName: string) => {
            this.addCustomListener(eventName, (event: Event) => this.handleMove(eventName, event));
        });
        this.addCustomListener("ak-dual-select-move", () => {
            this.requestUpdate();
        });
    }

    get value() {
        return this.selected;
    }

    handleMove(eventName: string, event: Event) {
        switch (eventName) {
            case EVENT_ADD_SELECTED: {
                this.addSelected();
                break;
            }
            case EVENT_REMOVE_SELECTED: {
                this.removeSelected();
                break;
            }
            case EVENT_ADD_ALL: {
                this.addAllVisible();
                break;
            }
            case EVENT_REMOVE_ALL: {
                this.removeAllVisible();
                break;
            }
            case EVENT_DELETE_ALL: {
                this.removeAll();
                break;
            }
            case EVENT_ADD_ONE: {
                this.addOne(event.detail);
                break;
            }
            case EVENT_REMOVE_ONE: {
                this.removeOne(event.detail);
                break;
            }

            default:
                throw new Error(
                    `AkDualSelect.handleMove received unknown event type: ${eventName}`
                );
        }
        this.dispatchCustomEvent("change", { value: this.selected });
        event.stopPropagation();
    }

    addSelected() {
        if (this.availablePane.value!.moveable.length === 0) {
            return;
        }
        const options = new Map(this.options);
        const selected = new Map(this.selected);
        this.availablePane.value!.moveable.forEach((key) => {
            const value = options.get(key);
            if (value) {
                selected.set(key, value);
            }
        });
        this.selected = Array.from(selected.entries()).sort();
        this.availablePane.value!.clearMove();
    }

    addOne(key: string) {
        const requested = this.options.find(([k, _]) => k === key);
        if (requested) {
            this.selected = Array.from(new Map([...this.selected, requested]).entries()).sort();
        }
    }

    removeOne(key: string) {
        this.selected = this.selected.filter(([k, _]) => k !== key);
    }

    // You must remember, these are the *currently visible* options; the parent node is responsible
    // for paginating and updating the list of currently visible options;
    addAllVisible() {
        const selected = new Map([...this.options, ...this.selected]);
        this.selected = Array.from(selected.entries()).sort();
        this.availablePane.value!.clearMove();
    }

    removeSelected() {
        if (this.selectedPane.value!.moveable.length === 0) {
            return;
        }
        const deselected = new Set(this.selectedPane.value!.moveable);
        this.selected = this.selected.filter(([key, _]) => !deselected.has(key));
        this.selectedPane.value!.clearMove();
    }

    // Remove all the items from selected that are in the *currently visible* options list
    removeAllVisible() {
        const options = new Set(this.options.map(([k, _]) => k));
        this.selected = this.selected.filter(([k, _]) => !options.has(k));
        this.selectedPane.value!.clearMove();
    }

    removeAll() {
        this.selected = [];
        this.selectedPane.value!.clearMove();
    }

    selectedKeys() {
        return new Set(this.selected.map(([k, _]) => k));
    }

    get canAddAll() {
        // False unless any visible option cannot be found in the selected list, so can still be
        // added.
        const selected = this.selectedKeys();
        return this.options.length > 0 && !!this.options.find(([key, _]) => !selected.has(key));
    }

    get canRemoveAll() {
        // False if no visible option can be found in the selected list
        const selected = this.selectedKeys();
        return this.options.length > 0 && !!this.options.find(([key, _]) => selected.has(key));
    }

    get needPagination() {
        return (this.pages?.next ?? 0) > 0 || (this.pages?.previous ?? 0) > 0;
    }

    render() {
        const selected = this.selectedKeys();
        const availableCount = this.availablePane.value?.toMove.size ?? 0;
        const selectedCount = this.selectedPane.value?.toMove.size ?? 0;
        const selectedTotal = this.selected.length;
        const availableStatus =
            availableCount > 0 ? msg(str`${availableCount} items marked to add.`) : "&nbsp;";
        const selectedTotalStatus = msg(str`${selectedTotal} items selected.`);
        const selectedCountStatus =
            selectedCount > 0 ? "  " + msg(str`${selectedCount} items marked to remove.`) : "";
        const selectedStatus = `${selectedTotalStatus}${selectedCountStatus}`;

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
                        .selected=${selected}
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

                    <div class="pf-c-dual-list-selector__status">
                        <span
                            class="pf-c-dual-list-selector__status-text"
                            id="basic-available-status-text"
                            >${unsafeHTML(selectedStatus)}</span
                        >
                    </div>

                    <ak-dual-select-selected-pane
                        ${ref(this.selectedPane)}
                        .selected=${this.selected}
                    ></ak-dual-select-selected-pane>
                </div>
            </div>
        `;
    }
}
