import { DrawerState, readDrawerParams } from "#elements/notifications/utils";

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKDrawerChangeEvent extends Event {
    public static readonly eventName = "ak-drawer-change";

    public readonly drawer: DrawerState;

    constructor(input: DrawerState) {
        super(AKDrawerChangeEvent.eventName, { bubbles: true, composed: true });

        this.drawer = input;
    }

    //#region Static Dispatchers

    /**
     * Dispatches an event to close the notification drawer.
     */
    public static dispatchCloseNotifications() {
        const params = {
            ...readDrawerParams(),
            notifications: false,
        };

        window.dispatchEvent(new AKDrawerChangeEvent(params));
    }

    /**
     * Dispatches an event to close the API drawer.
     */
    public static dispatchCloseAPI() {
        const params = {
            ...readDrawerParams(),
            api: false,
        };

        window.dispatchEvent(new AKDrawerChangeEvent(params));
    }

    /**
     * Dispatches an event to toggle the notification drawer.
     */
    public static dispatchNotificationsToggle() {
        const params = readDrawerParams();
        params.notifications = !params.notifications;

        window.dispatchEvent(new AKDrawerChangeEvent(params));
    }

    /**
     * Dispatches an event to toggle the API drawer.
     */
    public static dispatchAPIToggle() {
        const params = readDrawerParams();
        params.api = !params.api;

        window.dispatchEvent(new AKDrawerChangeEvent(params));
    }

    //#endregion
}

declare global {
    interface WindowEventMap {
        [AKDrawerChangeEvent.eventName]: AKDrawerChangeEvent;
    }
}
