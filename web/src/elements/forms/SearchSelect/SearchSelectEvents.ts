/**
 * class SearchSelectSelectEvent
 *
 * Intended meaning: the user selected an item from the entire dialogue, either by clicking on it
 * with the mouse, or selecting it with the keyboard controls and pressing Enter or Space.
 */
export class SearchSelectSelectEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-search-select-select", { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * class SearchSelectSelectMenuEvent
 *
 * Intended meaning: the user selected an item from the menu, either by clicking on it with the
 * mouse, or selecting it with the keyboard controls and pressing Enter or Space. This is
 * intercepted an interpreted internally, usually resulting in a throw of SearchSelectSelectEvent.
 * They have to be distinct to avoid an infinite event loop.
 */
export class SearchSelectSelectMenuEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-search-select-select-menu", { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * class SearchSelectCloseEvent
 *
 * Intended meaning: the user requested that the menu dropdown close. Usually triggered by pressing
 * the Escape key.
 */
export class SearchSelectCloseEvent extends Event {
    constructor() {
        super("ak-search-select-close", { composed: true, bubbles: true });
    }
}

/**
 * class SearchSelectInputEvent
 *
 * Intended meaning: the user made a change to the content of the `<input>` field
 */
export class SearchSelectInputEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-search-select-input", { composed: true, bubbles: true });
        this.value = value;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-search-select-select-menu": SearchSelectSelectMenuEvent;
        "ak-search-select-select": SearchSelectSelectEvent;
        "ak-search-select-input": SearchSelectInputEvent;
        "ak-search-select-close": SearchSelectCloseEvent;
    }
}
