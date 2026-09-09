import "#elements/Tabs";
import "#elements/a11y/ak-skip-to-content";
import "#user/requests/BrowseRequestable";
import "#user/requests/MyGrantRequestsList";
import "#user/requests/PendingReviewList";

import { aki } from "#common/api/client";
import { PaginatedResponse } from "#common/api/responses";

import { AKSkipToContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { paramURL } from "#elements/router/RouterOutlet";
import { SlottedTemplateResult } from "#elements/types";

import { AccessRequestFulfillForm } from "#user/requests/AccessRequestFulfillForm";
import Styles from "#user/user-settings/styles.css";

import { GrantRequest, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-access-requests-page")
export class AccessRequestsPage extends AKElement {
    static styles: CSSResult[] = [PFPage, PFBanner, PFContent, Styles];

    @state()
    toReview?: PaginatedResponse<GrantRequest>;

    @property({ attribute: "request-to-fulfill" })
    requestToFulfill: string | null = null;

    override async connectedCallback(): Promise<void> {
        super.connectedCallback();
        try {
            this.toReview = await aki(RequestsApi).requestsGrantRequestsPendingReviewList({});
        } catch (error) {
            showAPIErrorMessage(error);
        }
    }

    protected updated(changedProperties: PropertyValues): void {
        super.updated(changedProperties);
        if (changedProperties.has("requestToFulfill") && this.requestToFulfill !== null) {
            aki(RequestsApi)
                .requestsGrantRequestsRetrieve({
                    uuid: this.requestToFulfill,
                })
                .then((req) => {
                    const form = new AccessRequestFulfillForm();
                    form.request = req;
                    form.showModal();
                });
        }
    }

    protected override render(): SlottedTemplateResult {
        return html`<div class="pf-c-page">
            <div class="pf-c-page__main">
                ${(this.toReview?.pagination.count || 0) > 0
                    ? html`<div class="pf-c-banner pf-m-info">
                          ${msg("Requests to review: ")}
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
                        class="pf-c-page__main-section pf-m-no-padding"
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
