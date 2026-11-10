import { renderDefault } from "../EventInfo.shared";

import { EventContext, EventWithContext } from "#common/events";

import { msg } from "@lit/localize";
import { html } from "lit";

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
- authentik version: ${import.meta.env.AK_VERSION}
- Deployment: [e.g. docker-compose, helm]

**Additional context**
Add any other context about the problem here.
        `;

function buildGitHubIssueUrl(context: EventContext): string {
    const httpRequest = context.http_request as EventContext;
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

export function renderSystemException(event: EventWithContext) {
    return html`<div class="pf-l-flex">
            <div class="pf-l-flex__item">
                <div class="pf-c-card__title">${msg("Exception")}</div>
                <div class="pf-c-card__title">
                    <a
                        class="pf-c-button pf-m-primary"
                        target="_blank"
                        href=${buildGitHubIssueUrl(event.context)}
                    >
                        ${msg("Open issue on GitHub...")}
                    </a>
                </div>
                <div class="pf-c-card__body">
                    <pre>${event.context.message}</pre>
                </div>
            </div>
        </div>
        <ak-expand>${renderDefault(event)}</ak-expand>`;
}
