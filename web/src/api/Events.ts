import { DefaultClient, PBResponse, QueryArguments } from "./Client";

export interface EventUser {
    pk: number;
    email?: string;
    username: string;
    on_behalf_of?: EventUser;
}

export interface EventContext {
    [key: string]: EventContext | string | number;
}

export class Event {
    pk: string;
    user: EventUser;
    action: string;
    app: string;
    context: EventContext;
    client_ip: string;
    created: string;

    constructor() {
        throw Error();
    }

    static get(pk: string): Promise<Event> {
        return DefaultClient.fetch<Event>(["events", "events", pk]);
    }

    static list(filter?: QueryArguments): Promise<PBResponse<Event>> {
        return DefaultClient.fetch<PBResponse<Event>>(["events", "events"], filter);
    }

    // events/events/top_per_user/?filter_action=authorize_application
    static topForUser(action: string): Promise<TopNEvent[]> {
        return DefaultClient.fetch<TopNEvent[]>(["events", "events", "top_per_user"], {
            "filter_action": action,
        });
    }
}

export interface TopNEvent {
    application: { [key: string]: string};
    counted_events: number;
    unique_users: number;
}
