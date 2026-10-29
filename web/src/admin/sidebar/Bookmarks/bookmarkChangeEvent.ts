export interface BookmarkChangeEventInit {
    label: string;
    path: string;
    add?: boolean;
}

export class BookmarkChangeEvent extends Event {
    static readonly eventName = "ak-bookmark-changed";

    readonly label: string;
    readonly path: string;
    readonly add: boolean;

    constructor({ add, path, label }: BookmarkChangeEventInit) {
        super(BookmarkChangeEvent.eventName, { bubbles: true, composed: true });
        this.label = label;
        this.path = path;
        this.add = Boolean(add);
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [BookmarkChangeEvent.eventName]: BookmarkChangeEvent;
    }
}
