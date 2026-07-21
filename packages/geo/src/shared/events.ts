import { EventActions } from "@goauthentik/api/src/models/EventActions.ts";

export type EventActionsRecord = { [key in EventActions]?: string };
