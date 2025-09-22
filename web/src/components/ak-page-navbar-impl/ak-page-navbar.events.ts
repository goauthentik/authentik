import { PageHeaderInit } from "./ak-page-navbar.types";

export class PageDetailsUpdate extends Event {
    static readonly eventName = "ak-page-details-update";
    header: PageHeaderInit;

    constructor(header: PageHeaderInit) {
        super(PageDetailsUpdate.eventName, { bubbles: true, composed: true });
        this.header = header;
    }
}

export class PageNavMenuToggle extends Event {
    static readonly eventName = "ak-page-nav-menu-toggle";
    open: boolean;

    constructor(open?: boolean) {
        super(PageNavMenuToggle.eventName, { bubbles: true, composed: true });
        this.open = !!open;
    }
}

export function setPageDetails(header: PageHeaderInit) {
    window.dispatchEvent(new PageDetailsUpdate(header));
}

declare global {
    interface GlobalEventHandlersEventMap {
        [PageDetailsUpdate.eventName]: PageDetailsUpdate;
        [PageNavMenuToggle.eventName]: PageNavMenuToggle;
    }
}
