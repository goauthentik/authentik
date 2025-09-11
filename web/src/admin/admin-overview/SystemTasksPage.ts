import "#components/ak-page-header";
import "#elements/Tabs";
import "#elements/buttons/ActionButton/index";
import "#elements/buttons/SpinnerButton/index";
import "#elements/events/LogViewer";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
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
        return html`<ak-page-header
                icon="pf-icon pf-icon-automation"
                header=${msg("System Tasks")}
                description=${msg(
                    "Long-running operations which authentik executes in the background.",
                )}
            ></ak-page-header>
            <ak-tabs>
                <section
                    slot="page-schedules"
                    data-tab-title="${msg("Schedules")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                        >
                            <ak-schedule-list></ak-schedule-list>
                        </div>
                    </div>
                </section>
                <section
                    slot="page-tasks"
                    data-tab-title="${msg("Tasks")}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-l-grid__item pf-m-12-col pf-m-12-col-on-xl pf-m-12-col-on-2xl"
                        >
                            <ak-task-list></ak-task-list>
                        </div>
                    </div>
                </section>
            </ak-tabs>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-system-tasks": SystemTasksPage;
    }
}
