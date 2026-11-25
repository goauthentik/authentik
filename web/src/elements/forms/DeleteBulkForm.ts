import "#elements/buttons/SpinnerButton/index";
import "#elements/entities/UsedByTable";
import { isNamedEntity } from "#common/api/entities";
import { EVENT_REFRESH } from "#common/constants";
import { parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { MessageLevel } from "#common/messages";
import { plural } from "#common/ui/locale/plurals";

import { ModalButton } from "#elements/buttons/ModalButton";
import { BulkDeleteMetadata } from "#elements/entities/UsedByTable";
import { showMessage } from "#elements/messages/MessageContainer";

import { UsedBy } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

/**
 * What confirming a {@linkcode DeleteBulkForm} does to the selected objects.
 */
export type BulkAction = "delete" | "remove" | "cancel";

/**
 * The wording a bulk action uses, given how many objects it covers and the singular and plural
 * names of their type.
 */
interface BulkActionMessages {
    heading(count: number, noun: string, nounPlural: string): string;
    confirmation(count: number, noun: string, nounPlural: string): string;
    success(count: number, noun: string, nounPlural: string): string;
    error(count: number, noun: string, nounPlural: string): string;
    submitLabel(count: number, noun: string, nounPlural: string): string;
}

const BulkActionMessageRecord: Record<BulkAction, BulkActionMessages> = {
    delete: {
        heading: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Delete ${formattedCount} ${noun}`, {
                        id: "bulk-action.delete.heading.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Delete ${formattedCount} ${nounPlural}`, {
                        id: "bulk-action.delete.heading.other",
                    }),
            }),
        confirmation: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Are you sure you want to delete ${formattedCount} ${noun}?`, {
                        id: "bulk-action.delete.confirmation.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Are you sure you want to delete ${formattedCount} ${nounPlural}?`, {
                        id: "bulk-action.delete.confirmation.other",
                    }),
            }),
        success: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Successfully deleted ${formattedCount} ${noun}.`, {
                        id: "bulk-action.delete.success.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Successfully deleted ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.delete.success.other",
                    }),
            }),
        error: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Failed to delete ${formattedCount} ${noun}.`, {
                        id: "bulk-action.delete.error.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Failed to delete ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.delete.error.other",
                    }),
            }),
        submitLabel: () => msg("Delete", { id: "bulk-action.delete.submit.label" }),
    },
    remove: {
        heading: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Remove ${formattedCount} ${noun}`, {
                        id: "bulk-action.remove.heading.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Remove ${formattedCount} ${nounPlural}`, {
                        id: "bulk-action.remove.heading.other",
                    }),
            }),
        confirmation: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Are you sure you want to remove ${formattedCount} ${noun}?`, {
                        id: "bulk-action.remove.confirmation.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Are you sure you want to remove ${formattedCount} ${nounPlural}?`, {
                        id: "bulk-action.remove.confirmation.other",
                    }),
            }),
        success: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Successfully removed ${formattedCount} ${noun}.`, {
                        id: "bulk-action.remove.success.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Successfully removed ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.remove.success.other",
                    }),
            }),
        error: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Failed to remove ${formattedCount} ${noun}.`, {
                        id: "bulk-action.remove.error.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Failed to remove ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.remove.error.other",
                    }),
            }),
        submitLabel: () => msg("Remove", { id: "bulk-action.remove.submit.label" }),
    },
    cancel: {
        heading: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Cancel ${formattedCount} ${noun}`, {
                        id: "bulk-action.cancel.heading.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Cancel ${formattedCount} ${nounPlural}`, {
                        id: "bulk-action.cancel.heading.other",
                    }),
            }),
        confirmation: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Are you sure you want to cancel ${formattedCount} ${noun}?`, {
                        id: "bulk-action.cancel.confirmation.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Are you sure you want to cancel ${formattedCount} ${nounPlural}?`, {
                        id: "bulk-action.cancel.confirmation.other",
                    }),
            }),
        success: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Successfully canceled ${formattedCount} ${noun}.`, {
                        id: "bulk-action.cancel.success.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Successfully canceled ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.cancel.success.other",
                    }),
            }),
        error: (count, noun, nounPlural) =>
            plural(count, {
                one: (formattedCount) =>
                    msg(str`Failed to cancel ${formattedCount} ${noun}.`, {
                        id: "bulk-action.cancel.error.one",
                    }),
                other: (formattedCount) =>
                    msg(str`Failed to cancel ${formattedCount} ${nounPlural}.`, {
                        id: "bulk-action.cancel.error.other",
                    }),
            }),
        // A plain "Cancel" would read as dismissing the dialog, so the button repeats the heading.
        submitLabel: (count, noun, nounPlural) =>
            BulkActionMessageRecord.cancel.heading(count, noun, nounPlural),
    },
};

/**
 * A confirmation dialog that applies one action, such as deleting, to every selected object.
 *
 * Its heading, confirmation prompt, and result messages come from {@linkcode action} and the
 * object type's names, pluralized for the number of objects.
 */
@customElement("ak-forms-delete-bulk")
export class DeleteBulkForm<T> extends ModalButton {
    @property({ attribute: false })
    public objects: T[] = [];

    @property({ type: String })
    public action: BulkAction = "delete";

    /**
     * Singular name of the objects' type.
     *
     * Defaults to the `verboseName` of the table or other named element that renders this form.
     */
    @property({ type: String, attribute: "verbose-name" })
    public verboseName: string | null = null;

    /**
     * Plural name of the objects' type.
     *
     * Defaults to the `verboseNamePlural` of the table or other named element that renders this
     * form.
     */
    @property({ type: String, attribute: "verbose-name-plural" })
    public verboseNamePlural: string | null = null;

    /**
     * Replaces the confirmation prompt, for actions that need to name what the objects are
     * removed from.
     */
    @property({ type: String, attribute: "action-subtext" })
    public actionSubtext: string | null = null;

    @property({ attribute: false })
    public metadata: (item: T) => BulkDeleteMetadata[] = (item: T) => {
        const rec = item as Record<string, unknown>;
        const meta: BulkDeleteMetadata[] = [];

        if (Object.hasOwn(rec, "name")) {
            meta.push({ key: msg("Name"), value: rec.name as string });
        }

        if (Object.hasOwn(rec, "pk")) {
            meta.push({ key: msg("ID"), value: rec.pk as string });
        }

        return meta;
    };

    @property({ attribute: false })
    public usedBy?: (item: T) => Promise<UsedBy[]>;

    @property({ attribute: false })
    public delete!: (item: T) => Promise<unknown>;

    /**
     * The message arguments shared by every string of the current action.
     */
    protected get messageArgs(): [count: number, noun: string, nounPlural: string] {
        const root = this.getRootNode();
        const host = root instanceof ShadowRoot && isNamedEntity(root.host) ? root.host : null;

        return [
            this.objects.length,
            this.verboseName ??
                host?.verboseName ??
                msg("Object", { id: "bulk-action.verbose-name.default.label" }),
            this.verboseNamePlural ??
                host?.verboseNamePlural ??
                msg("Objects", { id: "bulk-action.verbose-name-plural.default.label" }),
        ];
    }

    protected async confirm(): Promise<void> {
        const messages = BulkActionMessageRecord[this.action];
        const args = this.messageArgs;

        return Promise.all(this.objects.map((item) => this.delete(item)))
            .then(() => {
                showMessage({
                    message: messages.success(...args),
                    level: MessageLevel.success,
                });

                this.dispatchEvent(
                    new CustomEvent(EVENT_REFRESH, {
                        bubbles: true,
                        composed: true,
                    }),
                );

                this.open = false;
            })
            .catch((parsedError: unknown) => {
                return parseAPIResponseError(parsedError).then(() => {
                    showMessage({
                        message: messages.error(...args),
                        description: pluckErrorDetail(parsedError),
                        level: MessageLevel.error,
                    });
                });
            });
    }

    renderModalInner(): TemplateResult {
        const messages = BulkActionMessageRecord[this.action];
        const args = this.messageArgs;

        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${messages.heading(...args)}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <p class="pf-c-title">
                        ${this.actionSubtext ?? messages.confirmation(...args)}
                    </p>
                    <slot name="notice"></slot>
                </form>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <ak-used-by-table
                    .items=${this.objects}
                    .usedBy=${this.usedBy}
                    .metadata=${this.metadata}
                >
                </ak-used-by-table>
            </section>
            <fieldset class="ak-c-fieldset pf-c-modal-box__footer">
                <legend class="sr-only">${msg("Form actions")}</legend>
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-plain"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>

                <ak-spinner-button .callAction=${() => this.confirm()} class="pf-m-danger">
                    ${messages.submitLabel(...args)}
                </ak-spinner-button>
            </fieldset>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-forms-delete-bulk": DeleteBulkForm<object>;
    }
}
