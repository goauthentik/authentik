import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/ProxyForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Schedule, TasksApi } from "@goauthentik/api";

@customElement("ak-schedule-form")
export class ScheduleForm extends ModelForm<Schedule, string> {
    async loadInstance(pk: string): Promise<Schedule> {
        return await new TasksApi(DEFAULT_CONFIG).tasksSchedulesRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (!this.instance) {
            return "";
        }
        return msg("Successfully updated schedule.");
    }

    async send(data: Schedule): Promise<Schedule | void> {
        if (!this.instance) {
            return;
        }
        return await new TasksApi(DEFAULT_CONFIG).tasksSchedulesUpdate({
            id: this.instance.id,
            scheduleRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-text-input
                name="crontab"
                value=${ifDefined(this.instance?.crontab)}
                label=${msg("Crontab")}
                required
                help=${msg("Crontab")}
            ></ak-text-input>
            <ak-switch-input
                name="paused"
                label=${msg("Paused")}
                ?checked=${this.instance?.paused ?? false}
                help=${msg("Pause this schedule")}
            >
            </ak-switch-input>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-schedule-form": ScheduleForm;
    }
}
