/**
 * @file Dual select custom events.
 */

import { DualSelectEventType, type DualSelectPair, type SearchbarEventDetail } from "./types.ts";

/**
 * The `detail` each dual select event carries.
 */
export interface DualSelectEventDetailMap {
    [DualSelectEventType.AddSelected]: undefined;
    [DualSelectEventType.RemoveSelected]: undefined;
    [DualSelectEventType.AddAll]: undefined;
    [DualSelectEventType.RemoveAll]: undefined;
    [DualSelectEventType.DeleteAll]: undefined;
    [DualSelectEventType.AddOne]: string | number;
    [DualSelectEventType.RemoveOne]: string | number;
    [DualSelectEventType.Move]: undefined;
    [DualSelectEventType.MoveChanged]: Array<string | number>;
    [DualSelectEventType.Search]: string;
    [DualSelectEventType.Change]: { value: DualSelectPair[] };
}

/**
 * The dual select events that carry no `detail`, such as the move commands from the controls.
 */
export type DualSelectCommandEventType = {
    [K in DualSelectEventType]: DualSelectEventDetailMap[K] extends undefined ? K : never;
}[DualSelectEventType];

/**
 * An event dispatched by the dual select or one of its parts. Bubbles and crosses shadow roots.
 */
export class DualSelectEvent<
    K extends DualSelectEventType = DualSelectEventType,
> extends CustomEvent<DualSelectEventDetailMap[K]> {
    constructor(
        type: K,
        ...[detail]: DualSelectEventDetailMap[K] extends undefined
            ? []
            : [detail: DualSelectEventDetailMap[K]]
    ) {
        super(type, { bubbles: true, composed: true, detail });
    }
}

/**
 * Dispatched by `ak-search-bar` as the user types.
 */
export class SearchbarEvent extends CustomEvent<SearchbarEventDetail> {
    public static readonly eventName = "ak-search";

    constructor(detail: SearchbarEventDetail) {
        super(SearchbarEvent.eventName, { bubbles: true, composed: true, detail });
    }
}

type DualSelectEventMap = {
    [K in DualSelectEventType]: DualSelectEvent<K>;
};

declare global {
    interface GlobalEventHandlersEventMap extends DualSelectEventMap {
        [SearchbarEvent.eventName]: SearchbarEvent;
    }
}
