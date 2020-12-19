import { DefaultClient } from "./Client";

export class Event {
    // events/events/top_per_user/?filter_action=authorize_application
    static topForUser(action: string): Promise<TopNEvents[]> {
        return DefaultClient.fetch<TopNEvents[]>(["events", "events", "top_per_user"], {
            "filter_action": action,
        });
    }
}

export interface TopNEvents {
    application: { [key: string]: string};
    counted_events: number;
    unique_users: number;
}
