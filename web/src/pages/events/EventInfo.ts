import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { until } from "lit-html/directives/until";
import { ActionEnum, FlowsApi } from "authentik-api";
import "../../elements/Spinner";
import "../../elements/Expand";
import { PFSize } from "../../elements/Spinner";
import { EventContext, EventWithContext } from "../../api/Events";
import { DEFAULT_CONFIG } from "../../api/Config";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-event-info")
export class EventInfo extends LitElement {

    @property({attribute: false})
    event!: EventWithContext;

    static get styles(): CSSResult[] {
        return [PFBase, PFFlex, PFList, PFDescriptionList,
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
                iframe {
                    width: 100%;
                    height: 50rem;
                }
            `
        ];
    }

    getModelInfo(context: EventContext): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`UID`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.pk as string}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Name`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.name as string}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`App`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.app as string}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Model Name`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.model_name as string}</div>
                </dd>
            </div>
        </dl>`;
    }

    getEmailInfo(context: EventContext): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Message`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.message}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Subject`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.subject}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`From`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.from_email}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`To`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">
                        ${(context.to_email as string[]).map(to => {
                            return html`<li>${to}</li>`;
                        })}
                    </div>
                </dd>
            </div>
        </dl>`;
    }

    defaultResponse(): TemplateResult {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <h3>${t`Context`}</h3>
                    <code>${JSON.stringify(this.event?.context, null, 4)}</code>
                </div>
                <div class="pf-l-flex__item">
                    <h3>${t`User`}</h3>
                    <code>${JSON.stringify(this.event?.user, null, 4)}</code>
                </div>
            </div>`;
    }

    render(): TemplateResult {
        if (!this.event) {
            return html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`;
        }
        switch (this.event?.action) {
        case ActionEnum.ModelCreated:
        case ActionEnum.ModelUpdated:
        case ActionEnum.ModelDeleted:
            return html`
                <h3>${t`Affected model:`}</h3>
                ${this.getModelInfo(this.event.context?.model as EventContext)}
                `;
        case ActionEnum.AuthorizeApplication:
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${t`Authorized application:`}</h3>
                        ${this.getModelInfo(this.event.context.authorized_application as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Using flow`}</h3>
                        <span>${until(new FlowsApi(DEFAULT_CONFIG).flowsInstancesList({
                            flowUuid: this.event.context.flow as string,
                        }).then(resp => {
                            return html`<a href="#/flow/flows/${resp.results[0].slug}">${resp.results[0].name}</a>`;
                        }), html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`)}
                        </span>
                    </div>
                </div>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.EmailSent:
            return html`<h3>${t`Email info:`}</h3>
                ${this.getEmailInfo(this.event.context)}
                <ak-expand>
                    <iframe srcdoc=${this.event.context.body}></iframe>
                </ak-expand>`;
        case ActionEnum.SecretView:
            return html`
                <h3>${t`Secret:`}</h3>
                ${this.getModelInfo(this.event.context.secret as EventContext)}`;
        case ActionEnum.PropertyMappingException:
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${t`Exception`}</h3>
                        <code>${this.event.context.message || this.event.context.error}</code>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Expression`}</h3>
                        <code>${this.event.context.expression}</code>
                    </div>
                </div>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.PolicyException:
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${t`Binding`}</h3>
                        ${this.getModelInfo(this.event.context.binding as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Request`}</h3>
                        <ul class="pf-c-list">
                            <li>${t`Object`}: ${this.getModelInfo((this.event.context.request as EventContext).obj as EventContext)}</li>
                            <li><span>${t`Context`}: <code>${JSON.stringify((this.event.context.request as EventContext).context, null, 4)}</code></span></li>
                        </ul>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Exception`}</h3>
                        <code>${this.event.context.message || this.event.context.error}</code>
                    </div>
                </div>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.PolicyExecution:
            return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${t`Binding`}</h3>
                        ${this.getModelInfo(this.event.context.binding as EventContext)}
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Request`}</h3>
                        <ul class="pf-c-list">
                            <li>${t`Object`}: ${this.getModelInfo((this.event.context.request as EventContext).obj as EventContext)}</li>
                            <li><span>${t`Context`}: <code>${JSON.stringify((this.event.context.request as EventContext).context, null, 4)}</code></span></li>
                        </ul>
                    </div>
                    <div class="pf-l-flex__item">
                        <h3>${t`Result`}</h3>
                        <ul class="pf-c-list">
                            <li>${t`Passing`}: ${(this.event.context.result as EventContext).passing}</li>
                            <li>${t`Messages`}:
                                <ul class="pf-c-list">
                                    ${((this.event.context.result as EventContext).messages as string[]).map(msg => {
                                        return html`<li>${msg}</li>`;
                                    })}
                                </ul>
                            </li>
                        </ul>
                    </div>
                </div>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.ConfigurationError:
            return html`<h3>${this.event.context.message}</h3>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.UpdateAvailable:
            return html`<h3>${t`New version available!`}</h3>
                <a
                    target="_blank"
                    href="https://github.com/goauthentik/authentik/releases/tag/version%2F${this.event.context.new_version}">
                    ${this.event.context.new_version}
                </a>`;
        // Action types which typically don't record any extra context.
        // If context is not empty, we fall to the default response.
        case ActionEnum.Login:
            if ("using_source" in this.event.context) {
                return html`<div class="pf-l-flex">
                    <div class="pf-l-flex__item">
                        <h3>${t`Using source`}</h3>
                        ${this.getModelInfo(this.event.context.using_source as EventContext)}
                    </div>
                </div>`;
            }
            return this.defaultResponse();
        case ActionEnum.LoginFailed:
            return html`
                <h3>${t`Attempted to log in as ${this.event.context.username}`}</h3>
                <ak-expand>${this.defaultResponse()}</ak-expand>`;
        case ActionEnum.Logout:
            if (this.event.context === {}) {
                return html`<span>${t`No additional data available.`}</span>`;
            }
            return this.defaultResponse();
        default:
            return this.defaultResponse();
        }
    }

}
