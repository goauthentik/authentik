/**
 * @file Search select events.
 */

/**
 * Dispatched when the selection changes, whether the user chose an option or a fetch settled on a
 * preselected one.
 */
export class SearchSelectChangeEvent<T = unknown> extends CustomEvent<{ value: T | null }> {
    public static readonly eventName = "ak-change";

    constructor(value: T | null) {
        super(SearchSelectChangeEvent.eventName, {
            bubbles: true,
            composed: true,
            detail: { value },
        });
    }
}

/**
 * Dispatched when the user activates the pinned action item, e.g. "Create new...".
 */
export class SearchSelectActionEvent extends Event {
    public static readonly eventName = "ak-search-select-action";

    constructor() {
        super(SearchSelectActionEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [SearchSelectChangeEvent.eventName]: SearchSelectChangeEvent;
        [SearchSelectActionEvent.eventName]: SearchSelectActionEvent;
    }
}
