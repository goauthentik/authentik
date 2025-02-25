import type { SidebarHelp } from "./SidebarHelp.js";

export class SidebarHelpToggleEvent extends Event {
    static readonly eventName = "ak-sidebar-help-toggle-request";
    source: SidebarHelp;
    constructor(source: SidebarHelp) {
        super(SidebarHelpToggleEvent.eventName, { bubbles: true, composed: true });
        this.source = source;
    }
}

declare global {
    interface GlobalEventHandlersEventMap {
        [SidebarHelpToggleEvent.eventName]: SidebarHelpToggleEvent;
    }
}
