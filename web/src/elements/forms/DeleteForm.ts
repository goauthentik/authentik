import { EVENT_REFRESH } from "@goauthentik/web/constants";
import { ModalButton } from "@goauthentik/web/elements/buttons/ModalButton";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import { MessageLevel } from "@goauthentik/web/elements/messages/Message";
import { showMessage } from "@goauthentik/web/elements/messages/MessageContainer";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

@customElement("ak-forms-delete")
export class DeleteForm extends ModalButton {
    static get styles(): CSSResult[] {
        return super.styles.concat(PFList);
    }

    @property({ attribute: false })
    obj?: Record<string, unknown>;

    @property()
    objectLabel?: string;

    @property({ attribute: false })
    usedBy?: () => Promise<UsedBy[]>;

    @property({ attribute: false })
    delete!: () => Promise<unknown>;

    confirm(): Promise<void> {
        return this.delete()
            .then(() => {
                this.onSuccess();
                this.open = false;
                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            })
            .catch((e) => {
                this.onError(e);
                throw e;
            });
    }

    onSuccess(): void {
        showMessage({
            message: t`Successfully deleted ${this.objectLabel} ${this.obj?.name}`,
            level: MessageLevel.success,
        });
    }

    onError(e: Error): void {
        showMessage({
            message: t`Failed to delete ${this.objectLabel}: ${e.toString()}`,
            level: MessageLevel.error,
        });
    }

    renderModalInner(): TemplateResult {
        let objName = this.obj?.name;
        if (objName) {
            objName = ` "${objName}"`;
        } else {
            objName = "";
        }
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${t`Delete ${this.objectLabel}`}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-c-page__main-section pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p>${t`Are you sure you want to delete ${this.objectLabel} ${objName} ?`}</p>
                </form>
            </section>
            ${this.usedBy
                ? until(
                      this.usedBy().then((usedBy) => {
                          if (usedBy.length < 1) {
                              return html``;
                          }
                          return html`
                              <section
                                  class="pf-c-modal-box__body pf-c-page__main-section pf-m-light"
                              >
                                  <form class="pf-c-form pf-m-horizontal">
                                      <p>${t`The following objects use ${objName} `}</p>
                                      <ul class="pf-c-list">
                                          ${usedBy.map((ub) => {
                                              let consequence = "";
                                              switch (ub.action) {
                                                  case UsedByActionEnum.Cascade:
                                                      consequence = t`object will be DELETED`;
                                                      break;
                                                  case UsedByActionEnum.CascadeMany:
                                                      consequence = t`connecting object will be deleted`;
                                                      break;
                                                  case UsedByActionEnum.SetDefault:
                                                      consequence = t`reference will be reset to default value`;
                                                      break;
                                                  case UsedByActionEnum.SetNull:
                                                      consequence = t`reference will be set to an empty value`;
                                                      break;
                                              }
                                              return html`<li>
                                                  ${t`${ub.name} (${consequence})`}
                                              </li>`;
                                          })}
                                      </ul>
                                  </form>
                              </section>
                          `;
                      }),
                  )
                : html``}
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm();
                    }}
                    class="pf-m-danger"
                >
                    ${t`Delete`} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${t`Cancel`}
                </ak-spinner-button>
            </footer>`;
    }
}
