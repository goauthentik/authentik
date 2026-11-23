/**
 * Announces a routed tab group's active tab, so the interface can reflect it in
 * the document title (`My Requests - Discover - authentik`).
 *
 * Only path-routed groups dispatch it: their active tab is part of the URL, so
 * it names the page the user is on.
 */
export class ActiveTabChangeEvent extends Event {
    static readonly eventName = "ak-active-tab-change";

    /**
     * The active tab's label, or `null` when the group has no active tab.
     */
    public readonly label: string | null;

    constructor(label: string | null) {
        super(ActiveTabChangeEvent.eventName, { bubbles: true, composed: true });
        this.label = label;
    }
}

declare global {
    interface WindowEventMap {
        [ActiveTabChangeEvent.eventName]: ActiveTabChangeEvent;
    }
}
