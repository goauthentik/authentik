import { DefaultClient } from "./client";

export class AuditEvent {
    //audit/events/top_per_user/?filter_action=authorize_application
    static topForUser(action: string): Promise<TopNEvent[]> {
        return DefaultClient.fetch<TopNEvent[]>(["audit", "events", "top_per_user"], {
            "filter_action": action,
        });
    }
}

export interface TopNEvent {
    application: { [key: string]: string};
    counted_events: number;
    unique_users: number;
}
