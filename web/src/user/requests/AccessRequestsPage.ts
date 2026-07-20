import "#elements/Tabs";
import "#elements/a11y/ak-skip-to-content";
import "#user/requests/BrowseRequestable";
import "#user/requests/MyGrantRequestsList";
import "#user/requests/PendingReviewList";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { AKSkipToContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { paramURL } from "#elements/router/RouterOutlet";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#user/user-settings/styles.css";

import { GrantRequest, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-access-requests-page")
export class AccessRequestsPage extends AKElement {
    static styles: CSSResult[] = [PFPage, PFBanner, PFContent, Styles];

    @state()
    toReview?: PaginatedResponse<GrantRequest>;

    override async connectedCallback(): Promise<void> {
        aki(RequestsApi)
            .requestsGrantRequestsPendingReviewList({})
            .then((rev) => {
                this.toReview = rev;
            })
            .finally(() => {
                super.connectedCallback();
            });
    }

    protected override render(): SlottedTemplateResult {
        return html`<div class="pf-c-page">
            <div class="pf-c-page__main">
                ${(this.toReview?.pagination.count || 0) > 0
                    ? html`<div class="pf-c-banner pf-m-info">
                          ${msg("Reviews to request: ")}
                          <a
                              href=${paramURL("/requests", {
                                  page: "page-for-review",
                              })}
                              >${msg("Review")}</a
                          >
                      </div>`
                    : nothing}
                <ak-tabs
                    role="main"
                    aria-label=${msg("Access requests")}
                    ${AKSkipToContent.ref}
                    vertical
                >
                    <div
                        id="page-browse"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-browse"
                        aria-label=${msg("Browse")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-browse-requestable></ak-browse-requestable>
                    </div>
                    <div
                        id="page-my-requests"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-my-requests"
                        aria-label=${msg("My Requests")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-my-grant-requests-list></ak-my-grant-requests-list>
                    </div>
                    <div
                        id="page-for-review"
                        role="tabpanel"
                        tabindex="0"
                        slot="page-for-review"
                        aria-label=${msg("For My Review")}
                        class="pf-c-page__main-section pf-m-no-padding-mobile"
                    >
                        <ak-pending-review-list></ak-pending-review-list>
                    </div>
                </ak-tabs>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-access-requests-page": AccessRequestsPage;
    }
}
