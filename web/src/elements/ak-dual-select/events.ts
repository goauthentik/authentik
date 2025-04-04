import { DualSelectPair } from "./types";

// Handled by the Server layer provider

// Request to provide a different page of the paginated results in the "available" panel.
export class DualSelectPaginatorNavEvent extends Event {
    static readonly eventName = "ak-dual-select-paginator-nav";
    constructor(public page: number = 0) {
        super(DualSelectPaginatorNavEvent.eventName, { bubbles: true, composed: true });
    }
}

// Request to provide a filtered collection for the "available" panel via a search string
export class DualSelectSearchEvent extends Event {
    static readonly eventName = "ak-dual-select-search";
    constructor(public search: string) {
        super(DualSelectSearchEvent.eventName, { bubbles: true, composed: true });
    }
}

// Request to update the "selected" list in the provider
export class DualSelectChangeEvent extends Event {
    static readonly eventName = "ak-dual-select-change";
    constructor(public selected: DualSelectPair[]) {
        super(DualSelectChangeEvent.eventName, { bubbles: true, composed: true });
    }
}

// Paginator and specific item events

export const moveEvents = [
    "add-all",
    "add-one",
    "add-selected",
    "delete-all",
    "remove-all",
    "remove-one",
    "remove-selected",
] as const;

export type MoveEventType = (typeof moveEvents)[number];

// Request to add or remove all, some, or just one item from the "selected" panel
export class DualSelectMoveRequestEvent extends Event {
    static readonly eventName = "ak-dual-select-request-move";
    constructor(
        public move: MoveEventType,
        public key?: string,
    ) {
        super(DualSelectMoveRequestEvent.eventName, { bubbles: true, composed: true });
    }
}

// Update events

// Request to update the viewset
export class DualSelectUpdateEvent extends Event {
    static readonly eventName = "ak-dual-select-update";
    constructor() {
        super(DualSelectUpdateEvent.eventName, { bubbles: true, composed: true });
    }
}

interface DualSelectMoveChangedEvent {
    keys: string[];
}

// Request to update the list of "marked for move" items in the "available" panel
export class DualSelectMoveAvailableEvent extends Event implements DualSelectMoveChangedEvent {
    static readonly eventName = "ak-dual-select-move-available";
    constructor(public keys: string[]) {
        super(DualSelectMoveAvailableEvent.eventName, { bubbles: true, composed: true });
    }
}

// Request to update the list of "marked for move" items in the "selected" panel
export class DualSelectMoveSelectedEvent extends Event implements DualSelectMoveChangedEvent {
    static readonly eventName = "ak-dual-select-move-selected";
    constructor(public keys: string[]) {
        super(DualSelectMoveSelectedEvent.eventName, { bubbles: true, composed: true });
    }
}

// Request to update either panel with a Filter
export class DualSelectPanelSearchEvent extends Event {
    static readonly eventName = "ak-dual-select-panel-search";
    constructor(
        public source: string,
        public filterOn: string,
    ) {
        super(DualSelectPanelSearchEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface HTMLElementEventMap {
        [DualSelectUpdateEvent.eventName]: DualSelectUpdateEvent;
        [DualSelectMoveAvailableEvent.eventName]: DualSelectMoveAvailableEvent;
        [DualSelectMoveSelectedEvent.eventName]: DualSelectMoveSelectedEvent;
        [DualSelectMoveRequestEvent.eventName]: DualSelectMoveRequestEvent;
        [DualSelectPaginatorNavEvent.eventName]: DualSelectPaginatorNavEvent;
        [DualSelectSearchEvent.eventName]: DualSelectSearchEvent;
        [DualSelectChangeEvent.eventName]: DualSelectChangeEvent;
        [DualSelectPanelSearchEvent.eventName]: DualSelectPanelSearchEvent;
    }

    interface WindowEventMap {
        [DualSelectMoveRequestEvent.eventName]: DualSelectMoveRequestEvent;
        [DualSelectPaginatorNavEvent.eventName]: DualSelectPaginatorNavEvent;
        [DualSelectMoveSelectedEvent.eventName]: DualSelectMoveSelectedEvent;
    }
}
