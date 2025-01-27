import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "@goauthentik/common/constants";
import { authentikEnterpriseContext } from "@goauthentik/elements/AuthentikContexts";
import type { ReactiveElementHost } from "@goauthentik/elements/types.js";

import { ContextProvider } from "@lit/context";
import type { ReactiveController } from "lit";

import type { LicenseSummary } from "@goauthentik/api";
import { EnterpriseApi } from "@goauthentik/api";

import type { AkAuthenticatedInterface } from "./Interface";

export class EnterpriseContextController implements ReactiveController {
    host!: ReactiveElementHost<AkAuthenticatedInterface>;

    context!: ContextProvider<{ __context__: LicenseSummary | undefined }>;

    constructor(host: ReactiveElementHost<AkAuthenticatedInterface>) {
        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: authentikEnterpriseContext,
            initialValue: undefined,
        });
        this.fetch = this.fetch.bind(this);
        this.fetch();
    }

    fetch() {
        new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseSummaryRetrieve().then((enterprise) => {
            this.context.setValue(enterprise);
            this.host.licenseSummary = enterprise;
        });
    }

    hostConnected() {
        window.addEventListener(EVENT_REFRESH_ENTERPRISE, this.fetch);
    }

    hostDisconnected() {
        window.removeEventListener(EVENT_REFRESH_ENTERPRISE, this.fetch);
    }

    hostUpdate() {
        // If the Interface changes its config information, we should notify all
        // users of the context of that change, without creating an infinite
        // loop of resets.
        if (this.host.licenseSummary !== this.context.value) {
            this.context.setValue(this.host.licenseSummary);
        }
    }
}
