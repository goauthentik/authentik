import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { Event, EventContext } from "../../api/Events";
import { Flow } from "../../api/Flows";
import { COMMON_STYLES } from "../../common/styles";
import "../../elements/Spinner";
import { SpinnerSize } from "../../elements/Spinner";

@customElement("ak-event-info")
export class EventInfo extends LitElement {

    @property({attribute: false})
    event?: Event;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                code {
                    display: block;
                    white-space: pre-wrap;
                }
                .pf-l-flex {
                    justify-content: space-between;
                }
                .pf-l-flex__item {
                    min-width: 25%;
                }
            `
        );
    }

    getModelInfo(context: EventContext): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }
        return html`<ul class="pf-c-list">
            <li>${gettext("UID")}: ${context.pk as string}</li>
            <li>${gettext("Name")}: ${context.name as string}</li>
            <li>${gettext("App")}: ${context.app as string}</li>
            <li>${gettext("Model Name")}: ${context.model_name as string}</li>
        </ul>`;
    }

    defaultResponse(): TemplateResult {
        return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Context")}</h3>
                        <code>${JSON.stringify(this.event?.context)}</code>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("User")}</h3>
                        <code>${JSON.stringify(this.event?.user)}</code>
                    </div>
                </div>`;
    }

    render(): TemplateResult {
        if (!this.event) {
            return html`<ak-spinner size=${SpinnerSize.Medium}></ak-spinner>`;
        }
        switch (this.event?.action) {
        case "model_created":
        case "model_updated":
        case "model_deleted":
            return html`
                <h3>${gettext("Affected model:")}</h3><hr>
                ${this.getModelInfo(this.event.context.model as EventContext)}
                `;
        case "authorize_application":
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Authorized application:")}</h3><hr>
                        ${this.getModelInfo(this.event.context.authorized_application as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Using flow")}</h3>
                        <span>${until(Flow.list({
        flow_uuid: this.event.context.flow as string,
    }).then(resp => {
        return html`<a href="#/flows/${resp.results[0].slug}">${resp.results[0].name}</a>`;
    }), html`<ak-spinner size=${SpinnerSize.Medium}></ak-spinner>`)}</span>
                    </div>
                </div>`;
        case "login_failed":
            return html`
                <h3>${gettext(`Attempted to log in as ${this.event.context.username}`)}</h3>
                `;
        case "token_view":
            return html`
                <h3>${gettext("Token:")}</h3><hr>
                ${this.getModelInfo(this.event.context.token as EventContext)}
                `;
        case "property_mapping_exception":
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Exception")}</h3>
                        <code>${this.event.context.error || this.event.context.message}</code>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Expression")}</h3>
                        <code>${this.event.context.expression}</code>
                    </div>
                </div>`;
        case "policy_exception":
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Binding")}</h3>
                        ${this.getModelInfo(this.event.context.binding as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Request")}</h3>
                        <ul class="pf-c-list">
                            <li>${gettext("Object")}: ${this.getModelInfo((this.event.context.request as EventContext).obj as EventContext)}</li>
                            <li><span>${gettext("Context")}: <code>${JSON.stringify((this.event.context.request as EventContext).context)}</code></span></li>
                        </ul>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Exception")}</h3>
                        <code>${this.event.context.error}</code>
                    </div>
                </div>`;
        case "policy_execution":
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Binding")}</h3>
                        ${this.getModelInfo(this.event.context.binding as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Request")}</h3>
                        <ul class="pf-c-list">
                            <li>${gettext("Object")}: ${this.getModelInfo((this.event.context.request as EventContext).obj as EventContext)}</li>
                            <li><span>${gettext("Context")}: <code>${JSON.stringify((this.event.context.request as EventContext).context)}</code></span></li>
                        </ul>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Result")}</h3>
                        <ul class="pf-c-list">
                            <li>${gettext("Passing")}: ${(this.event.context.result as EventContext).passing}</li>
                            <li>${gettext("Messages")}:
                                <ul class="pf-c-list">
                                    ${((this.event.context.result as EventContext).messages as string[]).map(msg => {
        return html`<li>${msg}</li>`;
    })}
                                </ul>
                            </li>
                        </ul>
                    </div>
                </div>`;
        case "configuration_error":
            return html`<h3>${this.event.context.message}</h3>`;
        case "update_available":
            return html`<h3>${gettext("New version available!")}</h3>
                <a target="_blank" href="https://github.com/BeryJu/authentik/releases/tag/version%2F${this.event.context.new_version}">${this.event.context.new_version}</a>
                `;
            // Action types which typically don't record any extra context.
            // If context is not empty, we fall to the default response.
        case "login":
            if ("using_source" in this.event.context) {
                return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${gettext("Using source")}</h3>
                        ${this.getModelInfo(this.event.context.using_source as EventContext)}
                    </div>
                </div>`;
            }
            return this.defaultResponse();
        case "logout":
            if (this.event.context === {}) {
                return html`<span>${gettext("No additional data available.")}</span>`;
            }
            return this.defaultResponse();
        default:
            return this.defaultResponse();
        }
    }

}
