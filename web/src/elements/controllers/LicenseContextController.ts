import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";
import { isGuest } from "#common/users";

import { ReactiveContextController } from "#elements/controllers/ReactiveContextController";
import { LicenseContext, LicenseMixin } from "#elements/mixins/license";
import { SessionMixin } from "#elements/mixins/session";
import type { ReactiveElementHost } from "#elements/types";

import { EnterpriseApi, LicenseSummary } from "@goauthentik/api";

import { ContextProvider } from "@lit/context";

export class LicenseContextController extends ReactiveContextController<LicenseSummary> {
    protected static refreshEvent = EVENT_REFRESH_ENTERPRISE;
    protected static logPrefix = "license";

    public host: ReactiveElementHost<SessionMixin & LicenseMixin>;
    public context: ContextProvider<LicenseContext>;

    constructor(host: ReactiveElementHost<LicenseMixin>, initialValue?: LicenseSummary) {
        super();

        this.host = host;
        this.context = new ContextProvider(this.host, {
            context: LicenseContext,
            initialValue: initialValue,
        });
    }

    protected apiEndpoint(requestInit?: RequestInit) {
        return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseSummaryRetrieve({}, requestInit);
    }

    protected doRefresh(licenseSummary: LicenseSummary) {
        this.context.setValue(licenseSummary);
        this.host.licenseSummary = licenseSummary;
    }

    public hostUpdate() {
        const { currentUser } = this.host;

        if (currentUser && !isGuest(currentUser) && !this.abortController) {
            this.refresh();

            return;
        }

        if (!currentUser && this.abortController) {
            this.abort("Session Invalidated");
        }
    }
}
