import { Event } from "./models";

export interface EventUser {
    pk: number;
    email?: string;
    username: string;
    on_behalf_of?: EventUser;
}

export interface EventContext {
    [key: string]: EventContext | string | number | string[];
}

export interface EventWithContext extends Event {
    user: EventUser;
    context: EventContext;
}
