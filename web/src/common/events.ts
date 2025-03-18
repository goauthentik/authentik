import { Event } from "@goauthentik/api";

export interface EventUser {
    pk: number;
    email?: string;
    username: string;
    on_behalf_of?: EventUser;
    is_anonymous?: boolean;
}

export interface EventGeo {
    city?: string;
    country?: string;
    continent?: string;
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

export interface EventContext {
    [key: string]: EventContext | EventModel | EventGeo | string | number | string[] | undefined;
    geo?: EventGeo;
}

export interface EventWithContext extends Event {
    user: EventUser;
    context: EventContext;
}
