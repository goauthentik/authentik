import { EventContext, EventContextProperty, EventModel, EventWithContext } from "#common/events";

import { SlottedTemplateResult } from "#elements/types";

import { renderDescriptionList } from "#components/DescriptionList";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

// TODO: Settle these types. It's too hard to make sense of what we're expecting here.
type EventSlotValueType =
    | number
    | SlottedTemplateResult
    | undefined
    | EventContext
    | EventContextProperty;

export type SectionFn = (label: string, body: SlottedTemplateResult) => SlottedTemplateResult;

export type FieldLabelTuple<V extends EventSlotValueType = EventSlotValueType> = [
    label: string,
    value: V,
];

export interface RenderArgs {
    event: EventWithContext;
    section: SectionFn;
}

export function getModelInfo(context: EventModel): TemplateResult {
    if (context === null) {
        return html`<span>-</span>`;
    }

    const modelFields: FieldLabelTuple[] = [
        [msg("UID"), context.pk],
        [msg("Name"), context.name],
        [msg("App"), context.app],
        [msg("Model Name"), context.model_name],
    ];

    return html`<div class="pf-c-card__body">
        ${renderDescriptionList(modelFields, { horizontal: true, compact: true })}
    </div>`;
}

export function getEmailInfo(context: EventContext): SlottedTemplateResult {
    if (context === null) {
        return html`<span>-</span>`;
    }

    const emailFields = [
        // ---
        [msg("Message"), context.message],
        [msg("Subject"), context.subject],
        [msg("From"), context.from_email],
        [
            msg("To"),
            html`${(context.to_email as string[]).map((to) => {
                return html`<li>${to}</li>`;
            })}`,
        ],
    ] satisfies FieldLabelTuple<EventSlotValueType>[];

    return renderDescriptionList(emailFields, { horizontal: true, compact: true });
}

export function renderDefault({ user, context }: EventWithContext): TemplateResult {
    return html`<div class="pf-l-flex">
        <div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("Context")}</div>
            <div class="pf-c-card__body">
                <ak-attribute-view show-count .value=${context}></ak-attribute-view>
            </div>
        </div>
        <div class="pf-l-flex__item">
            <div class="pf-c-card__title">${msg("User")}</div>
            <div class="pf-c-card__body">
                <ak-attribute-view show-count .value=${user}></ak-attribute-view>
            </div>
        </div>
    </div>`;
}
