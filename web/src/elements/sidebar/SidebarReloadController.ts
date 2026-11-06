import * as SidebarExpansion from "#elements/sidebar/expansion";
import { type Sidebar } from "#elements/sidebar/Sidebar";

import { ReactiveController } from "lit";

export class SidebarReloadController implements ReactiveController {
    constructor(protected host: Sidebar) {
        host.addController(this);
    }

    #save = () => {
        SidebarExpansion.writeState(Object.fromEntries(this.host.expanded));
    };

    hostConnected() {
        for (const [key, open] of Object.entries(SidebarExpansion.readState())) {
            this.host.expanded.set(key, open);
        }

        window.addEventListener("pagehide", this.#save);
    }

    hostDisconnected() {
        window.removeEventListener("pagehide", this.#save);
        this.#save();
    }

    hostUpdated() {
        this.#save();
    }
}
