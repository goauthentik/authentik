import "#elements/EmptyState";
import "./ak-library-impl.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIResult } from "#common/api/responses";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";

import { AKElement } from "#elements/Base";

import { Application, CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

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

@customElement("ak-library")
export class LibraryPage extends AKElement {
    static shadowRootOptions = { ...AKElement.shadowRootOptions, delegatesFocus: true };

    protected createRenderRoot(): HTMLElement | DocumentFragment {
        return this;
    }

    /**
     * The list of applications. This is the *complete* list; the constructor fetches as many pages
     * as the server announces when page one is accessed, and then concatenates them all together.
     */
    @state()
    protected apps: APIResult<Application[]> = {
        loading: true,
        error: null,
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        this.fetchApplications()
            .then((apps) => {
                this.apps = apps;
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);
                this.apps = {
                    loading: false,
                    error: parsedError,
                };
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
            (acc, result) => {
                if (result.status === "rejected") {
                    const reason = JSON.stringify(result.reason, null, 2);
                    throw new Error(`Could not retrieve list of applications. Reason: ${reason}`);
                }
                return [...acc, ...result.value.results];
            },
            [...applicationListFetch.results],
        );
    }

    public pageTitle = msg("My Applications");

    render() {
        if (this.apps.loading) {
            return html`<ak-empty-state default-label></ak-empty-state>`;
        }

        if (this.apps.error) {
            return html`<ak-empty-state icon="fa-ban"
                ><span>${msg("Failed to fetch applications.")}</span>
                <div slot="body">${pluckErrorDetail(this.apps.error)}</div>
            </ak-empty-state>`;
        }

        return html`<ak-library-impl .apps=${this.apps}></ak-library-impl>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library": LibraryPage;
    }
}
