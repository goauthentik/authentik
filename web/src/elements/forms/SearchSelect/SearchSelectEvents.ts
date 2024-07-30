/**
 * class SearchSelectSelectItemEvent
 *
 * Intended meaning: the user selected an item from the menu, either by clicking on it with the
 * mouse, or selecting it with the keyboard controls and pressing Enter or Space. This is
 * intercepted an interpreted internally, usually resulting in a throw of SearchSelectSelectEvent.
 * They have to be distinct to avoid an infinite event loop.
 */
export class SearchSelectSelectItemEvent extends Event {
    static readonly eventName = "ak-search-select-select-item";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(SearchSelectSelectItemEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * class SearchSelectRequestCloseEvent
 *
 * Intended meaning: the user requested to leave the menu dropdown. Usually triggered by pressing
 * the Escape key.
 */
export class SearchSelectRequestCloseEvent extends Event {
    static readonly eventName = "ak-search-select-close";
    constructor() {
        super(SearchSelectRequestCloseEvent.eventName, { composed: true, bubbles: true });
    }
}

/**
 * class SearchSelectInputEvent
 *
 * Intended meaning: the user made a change to the content of the `<input>` field
 */
export class SearchSelectInputEvent extends Event {
    static readonly eventName = "ak-search-select-input";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(SearchSelectInputEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

/**
 * class SearchSelectMenuLostFocus
 */
export class SearchSelectMenuLostFocusEvent extends Event {
    static readonly eventName = "ak-search-select-menu-lost-focus";
    constructor() {
        super(SearchSelectMenuLostFocusEvent.eventName, { composed: true, bubbles: true });
    }
}

/**
 * class SearchSelectChangeEvent
 *
 * Intended meaning: the actual value of the SearchSelect has changed.  This event communicates
 * this upward to consumers.
 */
export class SearchSelectChangeEvent extends Event {
    static readonly eventName = "ak-search-select-change";
    value: string | undefined;
    constructor(value: string | undefined) {
        super(SearchSelectInputEvent.eventName, { composed: true, bubbles: true });
        this.value = value;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [SearchSelectMenuLostFocusEvent.eventName]: SearchSelectMenuLostFocusEvent;
        [SearchSelectSelectItemEvent.eventName]: SearchSelectSelectItemEvent;
        [SearchSelectInputEvent.eventName]: SearchSelectInputEvent;
        [SearchSelectChangeEvent.eventName]: SearchSelectChangeEvent;
        [SearchSelectRequestCloseEvent.eventName]: SearchSelectRequestCloseEvent;
    }
}
