import { Event } from "@goauthentik/api";

export interface EventUser {
    pk: number;
    email?: string;
    username: string;
    on_behalf_of?: EventUser;
    is_anonymous?: boolean;
}

export interface EventContext {
    [key: string]: EventContext | EventModel | string | number | string[];
}

export interface EventWithContext extends Event {
    user: EventUser;
    context: EventContext;
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
