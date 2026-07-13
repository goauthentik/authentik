import "../../elements/AppIcon";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { PaginatedResponse } from "#elements/table/shared";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import {
    Application,
    CoreApi,
    GrantRequestCreateRequest,
    PamApi,
    Persona,
    PersonaTemplate,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css } from "lit";
import { html } from "lit-html";
import { customElement, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

@customElement("ak-discover-form")
export class DiscoverForm extends Form<GrantRequestCreateRequest> {
    public static override createLabel = null;
    public static submitVerb: string = msg("Request");

    static styles = [
        ...super.styles,
        PFCard,
        PFGrid,
        css`
            .pf-l-grid {
                padding: 1rem 0;
            }
        `,
    ];

    @state()
    apps?: PaginatedResponse<Application>;

    @state()
    selected: Application[] = [];

    @state()
    templates?: PaginatedResponse<PersonaTemplate>;

    @state()
    selectedTemplates: PersonaTemplate[] = [];

    @state()
    selectedPersona?: Persona;

    public override async connectedCallback(): Promise<void> {
        super.connectedCallback();

        this.apps = await aki(CoreApi).coreApplicationsRequestableList({});
        this.templates = await aki(PamApi).pamPersonaTemplatesList({});
    }

    protected send(_data: GrantRequestCreateRequest): Promise<unknown> {
        return aki(PamApi)
            .pamGrantRequestsCreate({
                grantRequestCreateRequest: {
                    pbms: [
                        ...this.selected.map((a) => a.pbmUuid),
                        ...this.selectedTemplates.map((t) => t.uuid!),
                    ],
                    persona: this.selectedPersona?.pk,
                },
            })
            .then((v) => {
                window.location.assign(v.link);
            });
    }

    protected renderForm(): SlottedTemplateResult | null {
        return html`<ak-form-element-horizontal label=${msg("Act as")} name="persona">
                <ak-search-select
                    placeholder=${msg("Myself")}
                    blankable
                    .fetchObjects=${async (query?: string): Promise<Persona[]> => {
                        const personas = await aki(PamApi).pamPersonasList({
                            ...(query !== undefined ? { search: query } : {}),
                        });
                        return personas.results;
                    }}
                    .renderElement=${(persona: Persona): string => {
                        return persona.username;
                    }}
                    .value=${(persona: Persona | undefined): string | undefined => {
                        return persona?.uuid;
                    }}
                    .selected=${(persona: Persona): boolean => {
                        return this.selectedPersona?.uuid === persona.uuid;
                    }}
                    @ak-change=${(ev: CustomEvent<{ value: Persona | null }>) => {
                        this.selectedPersona = ev.detail.value ?? undefined;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optionally request this access for one of your agent personas instead of yourself.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <div class="pf-l-grid pf-m-gutter">
                ${this.apps?.results.map((app) => {
                    return html`
                        <div
                            class="pf-l-grid__item pf-m-2-col pf-c-card pf-m-selectable-raised pf-m-compact ${this.selected.includes(
                                app,
                            )
                                ? "pf-m-selected-raised"
                                : ""}"
                            @click=${() => {
                                if (this.selected.includes(app)) {
                                    this.selected.splice(this.selected.indexOf(app), 1);
                                } else {
                                    this.selected.push(app);
                                }
                                this.requestUpdate();
                            }}
                        >
                            <ak-app-icon
                                exportparts="icon:card-header-icon"
                                size=${PFSize.Large}
                                name=${app.name}
                                icon=${ifPresent(app.metaIconUrl)}
                                .iconThemedUrls=${app.metaIconThemedUrls}
                            ></ak-app-icon>
                            <div role="heading" aria-level="2" class="pf-c-card__title">
                                ${app.name}
                            </div>
                        </div>
                    `;
                })}
            </div>
            ${this.templates && this.templates.results.length > 0
                ? html`<h2 class="pf-c-title pf-m-lg">${msg("Agent personas")}</h2>
                      <p class="pf-c-form__helper-text">
                          ${msg(
                              "Request a persona of your own from one of the templates below. It will show up under Agents once approved.",
                          )}
                      </p>
                      <div class="pf-l-grid pf-m-gutter">
                          ${this.templates.results.map((template) => {
                              return html`
                                  <div
                                      class="pf-l-grid__item pf-m-2-col pf-c-card pf-m-selectable-raised pf-m-compact ${this.selectedTemplates.includes(
                                          template,
                                      )
                                          ? "pf-m-selected-raised"
                                          : ""}"
                                      @click=${() => {
                                          if (this.selectedTemplates.includes(template)) {
                                              this.selectedTemplates.splice(
                                                  this.selectedTemplates.indexOf(template),
                                                  1,
                                              );
                                          } else {
                                              this.selectedTemplates.push(template);
                                          }
                                          this.requestUpdate();
                                      }}
                                  >
                                      <div class="pf-c-card__header">
                                          <i class="fas fa-robot fa-2x" aria-hidden="true"></i>
                                      </div>
                                      <div role="heading" aria-level="2" class="pf-c-card__title">
                                          ${template.name}
                                      </div>
                                  </div>
                              `;
                          })}
                      </div>`
                : html``} `;
    }
}
