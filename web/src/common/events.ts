import { Event as EventSerializer } from "@goauthentik/api";

/**
 * Event dispatched when the UI should refresh.
 */
export class AKRefreshEvent extends Event {
    public static readonly eventName = "ak-refresh";

    constructor() {
        super(AKRefreshEvent.eventName, { bubbles: true, composed: true });
    }
}

/**
 * Event dispatched when a change in enterprise features requires a refresh.
 */
export class AKEnterpriseRefreshEvent extends Event {
    public static readonly eventName = "ak-refresh-enterprise";

    constructor() {
        super(AKEnterpriseRefreshEvent.eventName, { bubbles: true, composed: true });
    }
}

export interface EventUser {
    pk: number;
    email?: string;
    username: string;
    is_anonymous?: boolean;
    on_behalf_of?: EventUser;
    authenticated_as?: EventUser;
}

export interface EventGeo {
    city?: string;
    country?: string;
    continent?: string;
    lat?: number;
    long?: number;
}

export interface EventModel {
    pk: string;
    name: string;
    app: string;
    model_name: string;
}

export interface EventRequest {
    path: string;
    method: string;
}

export type EventContextProperty = EventModel | EventGeo | string | number | string[] | undefined;

// TODO: Events should have more specific types.
export interface EventContext {
    [key: string]: EventContext | EventContextProperty;
    geo?: EventGeo;
    device?: EventModel;
}

export interface EventWithContext extends EventSerializer {
    user: EventUser;
    context: EventContext;
}
