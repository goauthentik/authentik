import "#elements/EmptyState";

import { aki } from "#common/api/client";
import { LayoutType } from "#common/ui/config";
import { groupBy } from "#common/utils";

import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#user/LibraryPage/ak-library-impl.css";
import { AKLibraryApplicationList } from "#user/LibraryPage/ApplicationList";
import AKLibraryApplicationListStyles from "#user/LibraryPage/ApplicationList.css";
import { ViewMode } from "#user/LibraryPage/types";

import { Application, CoreApi, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFCheck from "@patternfly/patternfly/components/Check/check.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

@customElement("ak-browse-requestable")
export class BrowseRequestable extends AKElement {
    static styles: CSSResult[] = [
        PFButton,
        PFCard,
        PFCheck,
        PFContent,
        PFList,
        PFStack,
        AKLibraryApplicationListStyles,
        Styles,
    ];

    #coreApi = aki(CoreApi);
    #requestsApi = aki(RequestsApi);

    @state()
    protected applications: Application[] = [];

    @state()
    protected loading = true;

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();
        await this.refresh();
    }

    protected async refresh(): Promise<void> {
        this.loading = true;
        try {
            const applications = await this.#coreApi.coreApplicationsRequestableList({
                pageSize: 100,
            });
            this.applications = applications.results;
        } catch (error) {
            showAPIErrorMessage(error);
        } finally {
            this.loading = false;
        }
    }

    protected override render(): SlottedTemplateResult {
        if (this.loading) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }
        if (this.applications.length < 1) {
            return html`<ak-empty-state icon="pf-icon-catalog"
                ><span>${msg("Nothing available to request.")}</span>
                <div slot="body">
                    ${msg("There's currently nothing you're eligible to request access to.")}
                </div>
            </ak-empty-state>`;
        }
        return AKLibraryApplicationList({
            editable: false,
            layout: LayoutType.row,
            viewMode: ViewMode.Grid,
            background: null,
            selectedApp: undefined,
            groupedApps: groupBy(this.applications, (app) => app.group || ""),
            onAppClick: async (app) => {
                try {
                    const { link } = await this.#requestsApi.requestsGrantRequestsCreate({
                        grantRequestCreateRequest: { pbms: [app.pbmUuid] },
                    });
                    window.location.assign(link);
                } catch (error) {
                    showAPIErrorMessage(error);
                }
            },
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-browse-requestable": BrowseRequestable;
    }
}
