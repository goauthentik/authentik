export class SearchSelectClickEvent extends Event {
    value: string | undefined;
    constructor(value: string | undefined) {
        super("ak-search-select-click", { composed: true, bubbles: true });
        this.value = value;
    }
}

export class SearchSelectCloseEvent extends Event {
    constructor() {
        super("ak-search-select-close", { composed: true, bubbles: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        "ak-search-select-click": SearchSelectClickEvent;
        "ak-search-select-close": SearchSelectCloseEvent;
    }
}
