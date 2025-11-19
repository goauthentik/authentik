import "#elements/buttons/SpinnerButton/index";

import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import PFList from "@patternfly/patternfly/components/List/list.css";

@customElement("ak-forms-delete")
export class DeleteForm extends ModalButton {
    static styles: CSSResult[] = [...super.styles, PFList];

    @property({ attribute: false })
    obj?: Record<string, unknown>;

    @property()
    objectLabel?: string;

    @property({ attribute: false })
    usedBy?: () => Promise<UsedBy[]>;

    @property({ attribute: false })
    delete!: () => Promise<unknown>;

    /**
     * Get the display name for the object being deleted/updated.
     */
    protected getObjectDisplayName(): string | undefined {
        return this.obj?.name as string | undefined;
    }

    /**
     * Get the formatted object name for display in messages.
     * Returns ` "displayName"` with quotes if display name exists, empty string otherwise.
     */
    protected getFormattedObjectName(): string {
        const displayName = this.getObjectDisplayName();
        return displayName ? ` "${displayName}"` : "";
    }

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
            .catch(async (error: unknown) => {
                await this.onError(error);

                throw error;
            });
    }

    onSuccess(): void {
        showMessage({
            message: msg(
                str`Successfully deleted ${this.objectLabel} ${this.getObjectDisplayName()}`,
            ),
            level: MessageLevel.success,
        });
    }

    onError(error: unknown): Promise<void> {
        return parseAPIResponseError(error).then((parsedError) => {
            showMessage({
                message: msg(
                    str`Failed to delete ${this.objectLabel}: ${pluckErrorDetail(parsedError)}`,
                ),
                level: MessageLevel.error,
            });
        });
    }

    renderModalInner(): TemplateResult {
        const objName = this.getFormattedObjectName();
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg(str`Delete ${this.objectLabel}`)}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p>
                        ${msg(str`Are you sure you want to delete ${this.objectLabel}${objName}?`)}
                    </p>
                </form>
            </section>
            ${this.usedBy
                ? until(
                      this.usedBy().then((usedBy) => {
                          if (usedBy.length < 1) {
                              return nothing;
                          }
                          return html`
                              <section class="pf-c-modal-box__body pf-m-light">
                                  <form class="pf-c-form pf-m-horizontal">
                                      <p>${msg(str`The following objects use ${objName}`)}</p>
                                      <ul class="pf-c-list">
                                          ${usedBy.map((ub) => {
                                              let consequence = "";
                                              switch (ub.action) {
                                                  case UsedByActionEnum.Cascade:
                                                      consequence = msg("object will be DELETED");
                                                      break;
                                                  case UsedByActionEnum.CascadeMany:
                                                      consequence = msg(
                                                          "connecting object will be deleted",
                                                      );
                                                      break;
                                                  case UsedByActionEnum.SetDefault:
                                                      consequence = msg(
                                                          "reference will be reset to default value",
                                                      );
                                                      break;
                                                  case UsedByActionEnum.SetNull:
                                                      consequence = msg(
                                                          "reference will be set to an empty value",
                                                      );
                                                      break;
                                              }
                                              return html`<li>
                                                  ${msg(str`${ub.name} (${consequence})`)}
                                              </li>`;
                                          })}
                                      </ul>
                                  </form>
                              </section>
                          `;
                      }),
                  )
                : nothing}
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm();
                    }}
                    class="pf-m-danger"
                >
                    ${msg("Delete")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-delete": DeleteForm;
    }
}
