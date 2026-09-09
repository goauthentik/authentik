import { RouteMatch } from "#elements/router/RouteMatch";

export class RouteChangeEvent extends Event {
    static readonly eventName = "ak-route-change";

    constructor(public readonly route: RouteMatch) {
        super(RouteChangeEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [RouteChangeEvent.eventName]: RouteChangeEvent;
    }
}
