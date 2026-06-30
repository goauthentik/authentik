import { aki } from "#common/api/client";
import { formatIntentLabel } from "#common/labels";

import { IconCopyButton } from "#elements/buttons/IconCopyButton";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Token } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { guard } from "lit-html/directives/guard.js";

export function IconTokenCopyButton(tokenLike?: Token | string | null): SlottedTemplateResult {
    return guard([tokenLike], () => {
        if (!tokenLike) {
            return null;
        }

        const { identifier, userObj, intent } =
            typeof tokenLike === "string"
                ? { identifier: tokenLike, userObj: null, intent: null }
                : tokenLike;

        const description = userObj?.username
            ? msg(str`${formatIntentLabel(intent)} token for ${userObj.username}`, {
                  id: "tokens.clipboard-copy.description",
                  desc: "Description for a clipboard copy action for tokens, with the token intent and username as variables.",
              })
            : undefined;

        const fetchTokenViewKey = (): Promise<Blob> => {
            if (!identifier) {
                console.warn("No identifier provided for IconTokenCopyButton");

                return Promise.resolve(new Blob([""], { type: "text/plain" }));
            }

            return aki(CoreApi)
                .coreTokensViewKeyRetrieve({ identifier })
                .then((tokenView) => new Blob([tokenView.key], { type: "text/plain" }));
        };

        return IconCopyButton({
            source: fetchTokenViewKey,
            buttonLabel: msg("Copy token", {
                id: "tokens.copy-button.label",
                desc: "Label for a button that copies a token to the clipboard.",
            }),
            entityLabel: msg("Token", {
                id: "tokens.copy-button.entity-label",
                desc: "Label for a token entity, used in clipboard copy success messages.",
            }),
            description,
        });
    });
}
