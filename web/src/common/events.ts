import { Event } from "@goauthentik/api";

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

export interface EventWithContext extends Event {
    user: EventUser;
    context: EventContext;
}
