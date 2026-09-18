import { EventActions } from "@goauthentik/api";

export type EventActionsRecord = { [key in EventActions]?: string };
