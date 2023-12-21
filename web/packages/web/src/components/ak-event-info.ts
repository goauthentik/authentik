import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { VERSION } from "@goauthentik/common/constants";
import { EventContext, EventModel, EventWithContext } from "@goauthentik/common/events";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Expand";
import "@goauthentik/elements/Spinner";
import { PFSize } from "@goauthentik/elements/Spinner";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { map } from "lit/directives/map.js";
import { until } from "lit/directives/until.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventActions, FlowsApi } from "@goauthentik/api";

type Pair = [string, string | number | EventContext | EventModel | string[] | TemplateResult];

// https://docs.github.com/en/issues/tracking-your-work-with-issues/creating-issues/about-automation-for-issues-and-pull-requests-with-query-parameters

// This is the template message body with our stacktrace passed to github via a querystring. It is
// 702 bytes long in UTF-8. [As of July
// 2023](https://saturncloud.io/blog/what-is-the-maximum-length-of-a-url-in-different-browsers/),
// the longest URL (not query string, **URL**) passable via this method is 2048 bytes. This is a bit
// of a hack, but it will get the top of the context across even if it exceeds the limit of the more
// restrictive browsers.

const githubIssueMessageBody = (context: EventContext) => `
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
- authentik version: ${VERSION}
- Deployment: [e.g. docker-compose, helm]

**Additional context**
Add any other context about the problem here.
        `;

@customElement("ak-event-info")
export class EventInfo extends AKElement {
    @property({ attribute: false })
    event!: EventWithContext;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFButton,
            PFFlex,
            PFCard,
            PFList,
            PFDescriptionList,
            css`
                code {
                    display: block;
                    white-space: pre-wrap;
                    word-break: break-all;
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

    renderDescriptionGroup([term, description]: Pair) {
        return html` <div class="pf-c-description-list__group">
            <dt class="pf-c-description-list__term">
                <span class="pf-c-description-list__text">${term}</span>
            </dt>
            <dd class="pf-c-description-list__description">
                <div class="pf-c-description-list__text">${description}</div>
            </dd>
        </div>`;
    }

    getModelInfo(context: EventModel): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }

        const modelFields: Pair[] = [
            [msg("UID"), context.pk],
            [msg("Name"), context.name],
            [msg("App"), context.app],
            [msg("Model Name"), context.model_name],
        ];

        return html`<div class="pf-c-card__body">
            <dl class="pf-c-description-list pf-m-horizontal">
                ${map(modelFields, this.renderDescriptionGroup)}
            </dl>
        </div>`;
    }

    getEmailInfo(context: EventContext): TemplateResult {
        if (context === null) {
            return html`<span>-</span>`;
        }

        // prettier-ignore
        const emailFields: Pair[] = [
            [msg("Message"), context.message],
            [msg("Subject"), context.subject],
            [msg("From"), context.from_email],
            [msg("To"), html`${(context.to_email as string[]).map((to) => {
                    return html`<li>${to}</li>`;
                })}`],
        ];

        return html`<dl class="pf-c-description-list pf-m-horizontal">
            ${map(emailFields, this.renderDescriptionGroup)}
        </dl>`;
    }

    renderDefaultResponse(): TemplateResult {
        return html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Context")}</div>
                <div class="pf-c-card__body">
                    <code>${JSON.stringify(this.event?.context, null, 4)}</code>
                </div>
            </div>
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("User")}</div>
                <div class="pf-c-card__body">
                    <code>${JSON.stringify(this.event?.user, null, 4)}</code>
                </div>
            </div>
        </div>`;
    }

    buildGitHubIssueUrl(context: EventContext): string {
        const httpRequest = this.event.context.http_request as EventContext;
        const title = httpRequest ? `${httpRequest?.method} ${httpRequest?.path}` : "";

        return [
            "https://github.com/goauthentik/authentik/issues/new",
            "?labels=bug,from_authentik",
            `&title=${encodeURIComponent(title)}`,
            `&body=${encodeURIComponent(githubIssueMessageBody(context))}`,
        ]
            .join("")
            .trim();
    }

    // It's commonplace not to put the return type on most functions in Typescript. In this case,
    // however, putting this return type creates a virtuous check of *all* the subrenderers to
    // ensure that all of them return what we're expecting.

    render(): TemplateResult {
        if (!this.event) {
            return html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`;
        }

        switch (this.event?.action) {
            case EventActions.ModelCreated:
            case EventActions.ModelUpdated:
            case EventActions.ModelDeleted:
                return this.renderModelChanged();

            case EventActions.AuthorizeApplication:
                return this.renderAuthorizeApplication();

            case EventActions.EmailSent:
                return this.renderEmailSent();

            case EventActions.SecretView:
                return this.renderSecretView();

            case EventActions.SystemException:
                return this.renderSystemException();

            case EventActions.PropertyMappingException:
                return this.renderPropertyMappingException();

            case EventActions.PolicyException:
                return this.renderPolicyException();

            case EventActions.PolicyExecution:
                return this.renderPolicyExecution();

            case EventActions.ConfigurationError:
                return this.renderConfigurationError();

            case EventActions.UpdateAvailable:
                return this.renderUpdateAvailable();

            // Action types which typically don't record any extra context.
            // If context is not empty, we fall to the default response.
            case EventActions.Login:
                return this.renderLogin();

            case EventActions.LoginFailed:
                return this.renderLoginFailed();

            case EventActions.Logout:
                return this.renderLogout();

            case EventActions.SystemTaskException:
                return this.renderSystemTaskException();

            default:
                return this.renderDefaultResponse();
        }
    }

    renderModelChanged() {
        return html`
            <div class="pf-c-card__title">${msg("Affected model:")}</div>
            <div class="pf-c-card__body">
                ${this.getModelInfo(this.event.context?.model as EventModel)}
            </div>
        `;
    }

    renderAuthorizeApplication() {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Authorized application:")}</div>
                    <div class="pf-c-card__body">
                        ${this.getModelInfo(
                            this.event.context.authorized_application as EventModel,
                        )}
                    </div>
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Using flow")}</div>
                    <div class="pf-c-card__body">
                        <span
                            >${until(
                                new FlowsApi(DEFAULT_CONFIG)
                                    .flowsInstancesList({
                                        flowUuid: this.event.context.flow as string,
                                    })
                                    .then((resp) => {
                                        return html`<a href="#/flow/flows/${resp.results[0].slug}"
                                            >${resp.results[0].name}</a
                                        >`;
                                    }),
                                html`<ak-spinner size=${PFSize.Medium}></ak-spinner>`,
                            )}
                        </span>
                    </div>
                </div>
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderEmailSent() {
        return html`<div class="pf-c-card__title">${msg("Email info:")}</div>
            <div class="pf-c-card__body">${this.getEmailInfo(this.event.context)}</div>
            <ak-expand>
                <iframe srcdoc=${this.event.context.body}></iframe>
            </ak-expand>`;
    }

    renderSecretView() {
        return html` <div class="pf-c-card__title">${msg("Secret:")}</div>
            ${this.getModelInfo(this.event.context.secret as EventModel)}`;
    }

    renderSystemException() {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Exception")}</div>
                    <div class="pf-c-card__title">
                        <a
                            class="pf-c-button pf-m-primary"
                            target="_blank"
                            href=${this.buildGitHubIssueUrl(this.event.context)}
                        >
                            ${msg("Open issue on GitHub...")}
                        </a>
                    </div>
                    <div class="pf-c-card__body">
                        <pre>${this.event.context.message}</pre>
                    </div>
                </div>
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderPropertyMappingException() {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Exception")}</div>
                    <div class="pf-c-card__body">
                        <pre>${this.event.context.message || this.event.context.error}</pre>
                    </div>
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Expression")}</div>
                    <div class="pf-c-card__body">
                        <code>${this.event.context.expression}</code>
                    </div>
                </div>
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderPolicyException() {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Binding")}</div>
                    ${this.getModelInfo(this.event.context.binding as EventModel)}
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Request")}</div>
                    <div class="pf-c-card__body">
                        <ul class="pf-c-list">
                            <li>
                                ${msg("Object")}:
                                ${this.getModelInfo(
                                    (this.event.context.request as EventContext).obj as EventModel,
                                )}
                            </li>
                            <li>
                                <span
                                    >${msg("Context")}:
                                    <code
                                        >${JSON.stringify(
                                            (this.event.context.request as EventContext).context,
                                            null,
                                            4,
                                        )}</code
                                    ></span
                                >
                            </li>
                        </ul>
                    </div>
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Exception")}</div>
                    <div class="pf-c-card__body">
                        <code>${this.event.context.message || this.event.context.error}</code>
                    </div>
                </div>
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderPolicyExecution() {
        return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Binding")}</div>
                    ${this.getModelInfo(this.event.context.binding as EventModel)}
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Request")}</div>
                    <div class="pf-c-card__body">
                        <ul class="pf-c-list">
                            <li>
                                ${msg("Object")}:
                                ${this.getModelInfo(
                                    (this.event.context.request as EventContext).obj as EventModel,
                                )}
                            </li>
                            <li>
                                <span
                                    >${msg("Context")}:
                                    <code
                                        >${JSON.stringify(
                                            (this.event.context.request as EventContext).context,
                                            null,
                                            4,
                                        )}</code
                                    ></span
                                >
                            </li>
                        </ul>
                    </div>
                </div>
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Result")}</div>
                    <div class="pf-c-card__body">
                        <ul class="pf-c-list">
                            <li>
                                ${msg("Passing")}:
                                ${(this.event.context.result as EventContext).passing}
                            </li>
                            <li>
                                ${msg("Messages")}:
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
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderConfigurationError() {
        return html`<div class="pf-c-card__title">${this.event.context.message}</div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderUpdateAvailable() {
        return html`<div class="pf-c-card__title">${msg("New version available")}</div>
            <a
                target="_blank"
                href="https://github.com/goauthentik/authentik/releases/tag/version%2F${this.event
                    .context.new_version}"
            >
                ${this.event.context.new_version}
            </a>`;
        // Action types which typically don't record any extra context.
        // If context is not empty, we fall to the default response.
    }

    renderLogin() {
        if ("using_source" in this.event.context) {
            return html`<div class="pf-l-flex">
                <div class="pf-l-flex__item">
                    <div class="pf-c-card__title">${msg("Using source")}</div>
                    ${this.getModelInfo(this.event.context.using_source as EventModel)}
                </div>
            </div>`;
        }
        return this.renderDefaultResponse();
    }

    renderLoginFailed() {
        return html` <div class="pf-c-card__title">
                ${msg(str`Attempted to log in as ${this.event.context.username}`)}
            </div>
            <ak-expand>${this.renderDefaultResponse()}</ak-expand>`;
    }

    renderLogout() {
        if (Object.keys(this.event.context).length === 0) {
            return html`<span>${msg("No additional data available.")}</span>`;
        }
        return this.renderDefaultResponse();
    }

    renderSystemTaskException() {
        return html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Exception")}</div>
                <div class="pf-c-card__body">
                    <pre>${this.event.context.message}</pre>
                </div>
            </div>
        </div>`;
    }
}
