export class PageChangeEvent extends Event {
    static readonly eventName = "ak-page-changed";
    readonly page: number;
    constructor(page: number) {
        super(PageChangeEvent.eventName, { bubbles: true, composed: true });
        this.page = page;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [PageChangeEvent.eventName]: PageChangeEvent;
    }
}
