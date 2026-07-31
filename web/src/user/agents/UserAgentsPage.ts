import "#elements/a11y/ak-skip-to-content";
import "#user/agents/UserAgentList";

import { AKSkipToContent } from "#elements/a11y/ak-skip-to-content";
import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#user/user-settings/styles.css";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-user-agents-page")
export class UserAgentsPage extends AKElement {
    static styles: CSSResult[] = [PFPage, PFContent, PFCard, Styles];

    protected override render(): SlottedTemplateResult {
        return html`<div class="pf-c-page">
            <main
                role="main"
                class="pf-c-page__main"
                aria-label=${msg("Agents", { id: "agent.verbose-name-plural.label" })}
                ${AKSkipToContent.ref}
            >
                <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">
                            ${msg("Agents", { id: "agent.verbose-name-plural.label" })}
                        </div>
                        <div class="pf-c-card__body">
                            <p>
                                ${msg(
                                    "Create expiring agent identities and hand their token to a harness so it can act on your behalf via the API.",
                                    { id: "agent.page.description" },
                                )}
                            </p>
                        </div>
                        <ak-user-agent-list></ak-user-agent-list>
                    </div>
                </section>
            </main>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-agents-page": UserAgentsPage;
    }
}
