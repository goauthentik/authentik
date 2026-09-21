import { pluckEntityName } from "#elements/entities/names";
import { LitFC } from "#elements/types";

import { UsedBy, UsedByActionEnum } from "@goauthentik/api";

import { match } from "ts-pattern";

import { msg, str } from "@lit/localize";
import { html } from "lit-html";

export function formatUsedByConsequence(usedBy: UsedBy, verboseName?: string): string {
    verboseName ||= msg("Object");

    return match(usedBy.action)
        .with(UsedByActionEnum.Cascade, () => {
            const relationName = usedBy.modelName || msg("Related object");

            return msg(str`${relationName} will be deleted`, {
                id: "used-by.consequence.cascade",
                desc: "Consequence of deletion, when the related object will also be deleted. The name of the related object will be included, in the format 'Related object will be deleted'.",
            });
        })
        .with(UsedByActionEnum.CascadeMany, () =>
            msg(str`Connection will be deleted`, {
                id: "used-by.consequence.cascade-many",
            }),
        )
        .with(UsedByActionEnum.SetDefault, () =>
            msg(str`Reference will be reset to default value`, {
                id: "used-by.consequence.set-default",
            }),
        )
        .with(UsedByActionEnum.SetNull, () =>
            msg(str`Reference will be set to an empty value`, {
                id: "used-by.consequence.set-null",
            }),
        )
        .with(UsedByActionEnum.LeftDangling, () =>
            msg(str`${verboseName} will be left dangling (may cause errors)`, {
                id: "used-by.consequence.left-dangling",
            }),
        )
        .with(UsedByActionEnum.UnknownDefaultOpenApi, () =>
            msg(str`${verboseName} has an unknown relationship (check logs)`, {
                id: "used-by.consequence.unknown-default-open-api",
            }),
        )
        .otherwise(() =>
            msg(str`${verboseName} has an unrecognized relationship (check logs)`, {
                id: "used-by.consequence.unrecognized",
            }),
        );
}

export interface UsedByListItemProps {
    ub: UsedBy;
    formattedName?: string;
    verboseName?: string | null;
}

export function formatUsedByMessage({
    ub,
    verboseName,
    formattedName,
}: UsedByListItemProps): string {
    verboseName ||= msg("Object");
    formattedName ||= pluckEntityName(ub) || msg("Unnamed");

    const consequence = formatUsedByConsequence(ub, verboseName);

    return msg(str`${formattedName} (${consequence})`, {
        id: "used-by-list-item",
        desc: "Used in list item, showing the name of the object and the consequence of deletion.",
    });
}

export const UsedByListItem: LitFC<UsedByListItemProps> = (props) => {
    return html`<li>${formatUsedByMessage(props)}</li>`;
};
