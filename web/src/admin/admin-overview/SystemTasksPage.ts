import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/events/LogViewer";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";

import { setPageDetails } from "#components/ak-page-navbar";

import { msg } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-system-tasks")
export class SystemTasksPage extends AKElement {
    static get styles(): CSSResult[] {
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

    render(): TemplateResult {
        return html`<main part="main">
            <ak-tabs part="tabs">
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-tasks"
                    id="page-tasks"
                    aria-label="${msg("Tasks")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <ak-task-list include-overview></ak-task-list>
                </div>
                <div
                    role="tabpanel"
                    tabindex="0"
                    slot="page-schedules"
                    id="page-schedules"
                    aria-label="${msg("Schedules")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <ak-schedule-list></ak-schedule-list>
                </div>
            </ak-tabs>
        </main>`;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-automation",
            header: msg("System Tasks"),
            description: msg("Long-running operations which authentik executes in the background."),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-system-tasks": SystemTasksPage;
    }
}
