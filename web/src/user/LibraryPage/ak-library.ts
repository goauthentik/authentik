import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { me } from "@goauthentik/common/users.js";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";

import { localized, msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { Application, CoreApi } from "@goauthentik/api";

import "./ak-library-impl.js";
import type { PageUIConfig } from "./types.js";

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

const coreApi = () => new CoreApi(DEFAULT_CONFIG);

@localized()
@customElement("ak-library")
export class LibraryPage extends AKElement {
    @state()
    ready = false;

    @state()
    isAdmin = false;

    /**
     * The list of applications. This is the *complete* list; the constructor fetches as many pages
     * as the server announces when page one is accessed, and then concatenates them all together.
     */
    @state()
    apps: Application[] = [];

    @state()
    uiConfig: PageUIConfig;

    constructor() {
        super();
        const uiConfig = rootInterface()?.uiConfig;
        if (!uiConfig) {
            throw new Error("Could not retrieve uiConfig. Reason: unknown. Check logs.");
        }

        this.uiConfig = {
            layout: uiConfig.layout.type,
            background: uiConfig.theme.cardBackground,
            searchEnabled: uiConfig.enabledFeatures.search,
        };

        Promise.all([this.fetchApplications(), me()]).then(([applications, meStatus]) => {
            this.isAdmin = meStatus.user.isSuperuser;
            this.apps = applications;
            this.ready = true;
        });
    }

    async fetchApplications(): Promise<Application[]> {
        const applicationListParams = (page = 1) => ({
            ordering: "name",
            page,
            pageSize: 100,
            onlyWithLaunchUrl: true,
        });

        const applicationListFetch = await coreApi().coreApplicationsList(applicationListParams(1));
        const pageCount = applicationListFetch.pagination.totalPages;
        if (pageCount === 1) {
            return applicationListFetch.results;
        }

        const applicationLaterPages = await Promise.allSettled(
            Array.from({ length: pageCount - 1 }).map((_a, idx) =>
                coreApi().coreApplicationsList(applicationListParams(idx + 2)),
            ),
        );

        return applicationLaterPages.reduce(
            function (acc, result) {
                if (result.status === "rejected") {
                    const reason = JSON.stringify(result.reason, null, 2);
                    throw new Error(`Could not retrieve list of applications. Reason: ${reason}`);
                }
                return [...acc, ...result.value.results];
            },
            [...applicationListFetch.results],
        );
    }

    pageTitle(): string {
        return msg("My Applications");
    }

    loading() {
        return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}> </ak-empty-state>`;
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-library": LibraryPage;
    }
}
