import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { VERSION } from "@goauthentik/common/constants";
import { EventContext, EventModel, EventWithContext } from "@goauthentik/common/events";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Expand";
import "@goauthentik/elements/Spinner";
import { PFSize } from "@goauthentik/elements/Spinner";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventActions, FlowsApi } from "@goauthentik/api";

@customElement("ak-event-info")
export class EventInfo extends AKElement {
    @property({ attribute: false })
    event!: EventWithContext;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFFlex,
            PFList,
            PFDescriptionList,
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
            `,
        ];
    }

    getModelInfo(context: EventModel): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }
        return html`<dl class="pf-c-description-list pf-m-horizontal">
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`UID`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.pk}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Name`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.name}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`App`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.app}</div>
                </dd>
            </div>
            <div class="pf-c-description-list__group">
                <dt class="pf-c-description-list__term">
                    <span class="pf-c-description-list__text">${t`Model Name`}</span>
                </dt>
                <dd class="pf-c-description-list__description">
                    <div class="pf-c-description-list__text">${context.model_name}</div>
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
                        ${(context.to_email as string[]).map((to) => {
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

    buildGitHubIssueUrl(context: EventContext): string {
        const httpRequest = this.event.context.http_request as EventContext;
        let title = "";
        if (httpRequest) {
            title = `${httpRequest?.method} ${httpRequest?.path}`;
        }
        // https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-issues/about-automation-for-issues-and-pull-requests-with-query-parameters
        const fullBody = `
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Logs**
<details>
    <summary>Stacktrace from authentik</summary>

\`\`\`
${context.message as string}
\`\`\`
</details>


**Version and Deployment (please complete the following information):**
- authentik version: ${VERSION()}
- Deployment: [e.g. docker-compose, helm]

**Additional context**
Add any other context about the problem here.
        `;
        return `https://github.com/goauthentik/authentik/issues/
new?labels=bug,from_authentik&title=${encodeURIComponent(title)}
&body=${encodeURIComponent(fullBody)}`.trim();
    }

    render(): TemplateResult {
        if (!this.event) {
            return html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`;
        }
        switch (this.event?.action) {
            case EventActions.ModelCreated:
            case EventActions.ModelUpdated:
            case EventActions.ModelDeleted:
                return html`
                    <h3>${t`Affected model:`}</h3>
                    ${this.getModelInfo(this.event.context?.model as EventModel)}
                `;
            case EventActions.AuthorizeApplication:
                return html`<div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`Authorized application:`}</h3>
                            ${this.getModelInfo(
                                this.event.context.authorized_application as EventModel,
                            )}
                        </div>
                        <div class="pf-l-flex__item">
                            <h3>${t`Using flow`}</h3>
                            <span
                                >${until(
                                    new FlowsApi(DEFAULT_CONFIG)
                                        .flowsInstancesList({
                                            flowUuid: this.event.context.flow as string,
                                        })
                                        .then((resp) => {
                                            return html`<a
                                                href="#/flow/flows/${resp.results[0].slug}"
                                                >${resp.results[0].name}</a
                                            >`;
                                        }),
                                    html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`,
                                )}
                            </span>
                        </div>
                    </div>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.EmailSent:
                return html`<h3>${t`Email info:`}</h3>
                    ${this.getEmailInfo(this.event.context)}
                    <ak-expand>
                        <iframe srcdoc=${this.event.context.body}></iframe>
                    </ak-expand>`;
            case EventActions.SecretView:
                return html` <h3>${t`Secret:`}</h3>
                    ${this.getModelInfo(this.event.context.secret as EventModel)}`;
            case EventActions.SystemException:
                return html` <a
                        class="pf-c-button pf-m-primary"
                        target="_blank"
                        href=${this.buildGitHubIssueUrl(this.event.context)}
                    >
                        ${t`Open issue on GitHub...`}
                    </a>
                    <div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`Exception`}</h3>
                            <code>${this.event.context.message}</code>
                        </div>
                    </div>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.PropertyMappingException:
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
            case EventActions.PolicyException:
                return html`<div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`Binding`}</h3>
                            ${this.getModelInfo(this.event.context.binding as EventModel)}
                        </div>
                        <div class="pf-l-flex__item">
                            <h3>${t`Request`}</h3>
                            <ul class="pf-c-list">
                                <li>
                                    ${t`Object`}:
                                    ${this.getModelInfo(
                                        (this.event.context.request as EventContext)
                                            .obj as EventModel,
                                    )}
                                </li>
                                <li>
                                    <span
                                        >${t`Context`}:
                                        <code
                                            >${JSON.stringify(
                                                (this.event.context.request as EventContext)
                                                    .context,
                                                null,
                                                4,
                                            )}</code
                                        ></span
                                    >
                                </li>
                            </ul>
                        </div>
                        <div class="pf-l-flex__item">
                            <h3>${t`Exception`}</h3>
                            <code>${this.event.context.message || this.event.context.error}</code>
                        </div>
                    </div>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.PolicyExecution:
                return html`<div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`Binding`}</h3>
                            ${this.getModelInfo(this.event.context.binding as EventModel)}
                        </div>
                        <div class="pf-l-flex__item">
                            <h3>${t`Request`}</h3>
                            <ul class="pf-c-list">
                                <li>
                                    ${t`Object`}:
                                    ${this.getModelInfo(
                                        (this.event.context.request as EventContext)
                                            .obj as EventModel,
                                    )}
                                </li>
                                <li>
                                    <span
                                        >${t`Context`}:
                                        <code
                                            >${JSON.stringify(
                                                (this.event.context.request as EventContext)
                                                    .context,
                                                null,
                                                4,
                                            )}</code
                                        ></span
                                    >
                                </li>
                            </ul>
                        </div>
                        <div class="pf-l-flex__item">
                            <h3>${t`Result`}</h3>
                            <ul class="pf-c-list">
                                <li>
                                    ${t`Passing`}:
                                    ${(this.event.context.result as EventContext).passing}
                                </li>
                                <li>
                                    ${t`Messages`}:
                                    <ul class="pf-c-list">
                                        ${(
                                            (this.event.context.result as EventContext)
                                                .messages as string[]
                                        ).map((msg) => {
                                            return html`<li>${msg}</li>`;
                                        })}
                                    </ul>
                                </li>
                            </ul>
                        </div>
                    </div>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.ConfigurationError:
                return html`<h3>${this.event.context.message}</h3>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.UpdateAvailable:
                return html`<h3>${t`New version available!`}</h3>
                    <a
                        target="_blank"
                        href="https://github.com/goauthentik/authentik/releases/tag/version%2F${this
                            .event.context.new_version}"
                    >
                        ${this.event.context.new_version}
                    </a>`;
            // Action types which typically don't record any extra context.
            // If context is not empty, we fall to the default response.
            case EventActions.Login:
                if ("using_source" in this.event.context) {
                    return html`<div class="pf-l-flex">
                        <div class="pf-l-flex__item">
                            <h3>${t`Using source`}</h3>
                            ${this.getModelInfo(this.event.context.using_source as EventModel)}
                        </div>
                    </div>`;
                }
                return this.defaultResponse();
            case EventActions.LoginFailed:
                return html` <h3>${t`Attempted to log in as ${this.event.context.username}`}</h3>
                    <ak-expand>${this.defaultResponse()}</ak-expand>`;
            case EventActions.Logout:
                if (Object.keys(this.event.context).length === 0) {
                    return html`<span>${t`No additional data available.`}</span>`;
                }
                return this.defaultResponse();
            default:
                return this.defaultResponse();
        }
    }
}
