import "#elements/EmptyState";
import "#user/requests/RequestEntitlementModal";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

import { aki } from "#common/api/client";
import { LayoutType } from "#common/ui/config";
import { groupBy } from "#common/utils";

import { AKElement } from "#elements/Base";
import { renderModal } from "#elements/dialogs";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#user/LibraryPage/ak-library-impl.css";
import { AKLibraryApplicationList } from "#user/LibraryPage/ApplicationList";
import AKLibraryApplicationListStyles from "#user/LibraryPage/ApplicationList.css";
import { ViewMode } from "#user/LibraryPage/types";
import { RequestApplicationForm } from "#user/requests/RequestApplicationForm";

import { Application, ApplicationTemplate, CoreApi, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-browse-requestable")
export class BrowseRequestable extends AKElement {
    static styles: CSSResult[] = [
        PFButton,
        PFCard,
        PFContent,
        PFPage,
        PFGallery,
        AKLibraryApplicationListStyles,
        Styles,
    ];

    #coreApi = aki(CoreApi);
    #requestsApi = aki(RequestsApi);

    @state()
    protected applications: Application[] = [];

    @state()
    protected templates: ApplicationTemplate[] = [];

    @state()
    protected loading = true;

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();
        await this.refresh();
    }

    protected async refresh(): Promise<void> {
        this.loading = true;

        try {
            const [applications, templates] = await Promise.all([
                this.#coreApi.coreApplicationsRequestableList({ pageSize: 100 }),
                this.#requestsApi.requestsApplicationTemplatesRequestableList({ pageSize: 100 }),
            ]);

            this.applications = applications.results;
            this.templates = templates.results;
        } catch (error) {
            showAPIErrorMessage(error);
        } finally {
            this.loading = false;
        }
    }

    #requestAccess = async (pbms: string[]): Promise<void> => {
        const { link } = await this.#requestsApi.requestsGrantRequestsCreate({
            grantRequestCreateRequest: { pbms },
        });

        if (link) {
            window.location.assign(link);
        }
    };

    #onAppClick = async (app: Application): Promise<void> => {
        try {
            const entitlements = await this.#coreApi.coreApplicationEntitlementsRequestableList({
                app: app.pk,
                pageSize: 100,
            });

            if (entitlements.results.length === 1) {
                await this.#requestAccess([entitlements.results[0].pbmUuid]);

                return;
            }

            if (entitlements.results.length > 1) {
                await renderModal(
                    html`<ak-request-entitlement-modal .app=${app}></ak-request-entitlement-modal>`,
                    { invokerElement: this },
                );

                return;
            }

            await this.#requestAccess([app.pbmUuid]);
        } catch (error) {
            showAPIErrorMessage(error);
        }
    };

    protected override render(): SlottedTemplateResult {
        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        if (this.applications.length < 1 && this.templates.length < 1) {
            return html`<ak-empty-state icon="pf-icon-catalog"
                ><span>${msg("Nothing available to request.")}</span>
                <div slot="body">
                    ${msg("There's currently nothing you're eligible to request access to.")}
                </div>
            </ak-empty-state>`;
        }

        return html`${this.renderApplications()}${this.renderTemplates()}`;
    }

    protected renderApplications(): SlottedTemplateResult {
        if (this.applications.length < 1) {
            return nothing;
        }

        return html`<div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__title">${msg("Requestable applications")}</h1>
            </div>
            ${AKLibraryApplicationList({
                editable: false,
                layout: LayoutType.row,
                viewMode: ViewMode.Grid,
                background: null,
                selectedApp: undefined,
                groupedApps: groupBy(this.applications, (app) => app.group || ""),
                onAppClick: this.#onAppClick,
            })}`;
    }

    protected renderTemplates(): SlottedTemplateResult {
        if (this.templates.length < 1) {
            return nothing;
        }

        return html`<div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__title">
                    ${msg("New applications", { id: "requests.browse.templates.header" })}
                </h1>
            </div>
            <div class="pf-c-content">
                <p>
                    ${msg(
                        "Request a new application for your team. Once approved, you get its client credentials under My Requests.",
                        { id: "requests.browse.templates.description" },
                    )}
                </p>
            </div>
            <div class="pf-l-gallery pf-m-gutter">
                ${this.templates.map(
                    (template) =>
                        html`<div class="pf-c-card">
                            <div class="pf-c-card__title">${template.name}</div>
                            <div class="pf-c-card__footer">
                                <button
                                    class="pf-c-button pf-m-primary"
                                    type="button"
                                    @click=${() => {
                                        const form = new RequestApplicationForm();
                                        form.template = template;

                                        return form.showModal();
                                    }}
                                >
                                    ${msg("Request", {
                                        id: "requests.request-application.submit-verb",
                                    })}
                                </button>
                            </div>
                        </div>`,
                )}
            </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-browse-requestable": BrowseRequestable;
    }
}
