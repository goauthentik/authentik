import { DEFAULT_CONFIG } from "#common/api/config";
import { PaginatedResponse } from "#common/api/responses";

import { AKElement } from "#elements/Base";

import { Application, CoreApi, PamApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-discovery")
export class DiscoverPage extends AKElement {
    static styles = [PFPage, PFForm, PFContent, PFFormControl];

    @state()
    apps?: PaginatedResponse<Application>;

    public override connectedCallback(): void {
        super.connectedCallback();

        new CoreApi(DEFAULT_CONFIG)
            .coreApplicationsList({
                superuserFullList: true,
            })
            .then((apps) => {
                this.apps = apps;
            });
    }

    render() {
        return html`<div class="pf-c-page__main">
            <div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__header pf-c-content">${msg("Discover")}</h1>
            </div>
            <main class="pf-c-page__main-section">
                <form
                    class="pf-c-form"
                    @submit=${(ev: SubmitEvent) => {
                        ev.preventDefault();
                        const data = new FormData(ev.target);
                        new PamApi(DEFAULT_CONFIG)
                            .pamGrantRequestsCreate({
                                grantRequestCreateRequest: {
                                    pbms: data.getAll("apps").map((x) => x.toString()),
                                },
                            })
                            .then((re) => {
                                window.location.assign(re.link);
                            });
                    }}
                >
                    ${this.apps?.results.map((app) => {
                        return html`
                            <div>
                                <input
                                    type="checkbox"
                                    id="app-${app.slug}"
                                    value=${app.pbmUuid}
                                    name="apps"
                                />
                                <label for="app-${app.slug}">${app.name}</label>
                            </div>
                        `;
                    })}
                    <input type="submit" />
                </form>
            </main>
        </div>`;
    }
}
