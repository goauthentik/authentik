import "@goauthentik/admin/applications/ApplicationAuthorizeChart";
import "@goauthentik/admin/applications/ApplicationCheckAccessForm";
import "@goauthentik/admin/applications/ApplicationForm";
import "@goauthentik/admin/policies/BoundPoliciesList";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-app-icon";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/rbac/ObjectPermissionsPage";

import { PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    Application,
    CoreApi,
    OutpostsApi,
    RbacPermissionsAssignedByUsersListModelEnum,
} from "@goauthentik/api";

import {
    ApplicationViewPageLoadingRenderer,
    ApplicationViewPageRenderer,
} from "./ApplicationViewPageRenderers.js";

@customElement("ak-application-view")
export class ApplicationViewPage extends AKElement {
    static get styles() {
        return [
            PFBase,
            PFList,
            PFBanner,
            PFPage,
            PFContent,
            PFButton,
            PFDescriptionList,
            PFGrid,
            PFCard,
        ];
    }

    @property({ type: String })
    applicationSlug?: string;

    @state()
    application?: Application;

    @state()
    missingOutpost = false;

    fetchIsMissingOutpost(providersByPk: Array<number>) {
        new OutpostsApi(DEFAULT_CONFIG)
            .outpostsInstancesList({
                providersByPk,
                pageSize: 1,
            })
            .then((outposts) => {
                if (outposts.pagination.count < 1) {
                    this.missingOutpost = true;
                }
            });
    }

    fetchApplication(slug: string) {
        new CoreApi(DEFAULT_CONFIG).coreApplicationsRetrieve({ slug }).then((app) => {
            this.application = app;
            if (
                app.providerObj &&
                [
                    RbacPermissionsAssignedByUsersListModelEnum.ProvidersProxyProxyprovider.toString(),
                    RbacPermissionsAssignedByUsersListModelEnum.ProvidersLdapLdapprovider.toString(),
                ].includes(app.providerObj.metaModelName)
            ) {
                this.fetchIsMissingOutpost([app.provider || 0]);
            }
        });
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("applicationSlug") && this.applicationSlug) {
            this.fetchApplication(this.applicationSlug);
        }
    }

    render() {
        const renderer = this.application
            ? new ApplicationViewPageRenderer(
                  this.application,
                  this.missingOutpost,
                  RbacPermissionsAssignedByUsersListModelEnum.CoreApplication,
              )
            : new ApplicationViewPageLoadingRenderer();

        return renderer.render();
    }
}
