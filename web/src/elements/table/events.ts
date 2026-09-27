import { TableLike } from "#elements/table/shared";

/**
 * Event dispatched when the table should refresh.
 */
export class AKTableRefreshEvent extends Event {
    public static readonly eventName = "ak-table-refresh";

    public readonly table: TableLike;

    constructor(table: TableLike) {
        super(AKTableRefreshEvent.eventName, { bubbles: true, composed: true });
        this.table = table;
    }
}

declare global {
    interface WindowEventMap {
        [AKTableRefreshEvent.eventName]: AKTableRefreshEvent;
    }
}
