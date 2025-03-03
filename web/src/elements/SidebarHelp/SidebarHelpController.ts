import { bound } from "@goauthentik/elements/decorators/bound";

import { LitElement, ReactiveController, ReactiveControllerHost } from "lit";

import { SidebarHelpToggleEvent } from "./events";

type ReactiveLitElement = LitElement & ReactiveControllerHost;

const DEFAULT_STYLE = "pf-m-width-default";

/**
 * A "Display documentation for this page" helper. Attach this controller to any element that
 * contains one or more SidebarHelp entries. It adjusts the width of the sidebar controller when
 * hidden to that of the button's *height*, since the button has been rotated 90° around a
 * corner-oriented axis.
 *
 * The events consumed by this component are not for general use.
 */

export class SidebarHelpController implements ReactiveController {
    host: ReactiveLitElement;

    constructor(host: ReactiveLitElement) {
        (this.host = host).addController(this);
    }

    @bound
    toggleHelpToggle(ev: SidebarHelpToggleEvent) {
        const { source } = ev;
        if (!source.showing) {
            source.classList.remove(source.activeStyle);
            source.classList.add(DEFAULT_STYLE);
            const { width } = source.button.getBoundingClientRect();
            source.style.setProperty("width", `${width}px`);
            return;
        }
        requestAnimationFrame(() => {
            source.style.removeProperty("width");
            source.classList.remove(DEFAULT_STYLE);
            source.classList.add(source.activeStyle);
        });
    }

    hostConnected() {
        this.host.addEventListener(SidebarHelpToggleEvent.eventName, this.toggleHelpToggle);
    }

    hostDisconnected() {
        this.host.removeEventListener(SidebarHelpToggleEvent.eventName, this.toggleHelpToggle);
    }
}
