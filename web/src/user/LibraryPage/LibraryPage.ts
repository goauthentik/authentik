import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { me } from "@goauthentik/common/users";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";

import { t } from "@lingui/macro";

import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { Application, CoreApi } from "@goauthentik/api";

import "./LibraryPageImpl";
import type { PageUIConfig } from "./types";

/**
 * List of Applications available
 *
 * Properties:
 * apps: a list of the applications available to the user.
 *
 * Aggregates two functions:
 *   - Display the list of applications available to the user
 *   - Filter that list using the search bar
 *
 */

@customElement("ak-library")
export class LibraryPage extends AKElement {
    @state()
    ready = false;

    @state()
    isAdmin = false;

    @state()
    apps!: PaginatedResponse<Application>;

    @state()
    uiConfig: PageUIConfig;

    constructor() {
        super();
        const applicationListFetch = new CoreApi(DEFAULT_CONFIG).coreApplicationsList({});
        const meFetch = me();
        const uiConfig = rootInterface()?.uiConfig;
        if (!uiConfig) {
            throw new Error("Could not retrieve uiConfig. Reason: unknown. Check logs.");
        }

        this.uiConfig = {
            layout: uiConfig.layout.type,
            background: uiConfig.theme.cardBackground,
            searchEnabled: uiConfig.enabledFeatures.search,
        };

        Promise.allSettled([applicationListFetch, meFetch]).then(
            ([applicationListStatus, meStatus]) => {
                if (meStatus.status === "rejected") {
                    throw new Error(
                        `Could not determine status of user. Reason: ${meStatus.reason}`,
                    );
                }
                if (applicationListStatus.status === "rejected") {
                    throw new Error(
                        `Could not retrieve list of applications. Reason: ${applicationListStatus.reason}`,
                    );
                }
                this.isAdmin = meStatus.value.user.isSuperuser;
                this.apps = applicationListStatus.value;
                this.ready = true;
            },
        );
    }

    pageTitle(): string {
        return t`My Applications`;
    }

    loading() {
        return html`<ak-empty-state ?loading="${true}" header=${t`Loading`}> </ak-empty-state>`;
    }

    running() {
        return html`<ak-library-impl
            ?isadmin=${this.isAdmin}
            .apps=${this.apps}
            .uiConfig=${this.uiConfig}
        ></ak-library-impl>`;
    }

    render() {
        return this.ready ? this.running() : this.loading();
    }
}
