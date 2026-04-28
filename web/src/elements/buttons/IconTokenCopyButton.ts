import { DEFAULT_CONFIG } from "#common/api/config";

import { IconCopyButton } from "#elements/buttons/IconCopyButton";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { guard } from "lit-html/directives/guard.js";

export function IconTokenCopyButton(identifier?: string | null): SlottedTemplateResult {
    return guard([], () => {
        const fetchTokenViewKey = (): Promise<Blob> => {
            if (!identifier) {
                console.warn("No identifier provided for IconTokenCopyButton");
                return Promise.resolve(new Blob([""], { type: "text/plain" }));
            }

            return new CoreApi(DEFAULT_CONFIG)
                .coreTokensViewKeyRetrieve({ identifier })
                .then((tokenView) => new Blob([tokenView.key], { type: "text/plain" }));
        };

        return IconCopyButton({
            source: fetchTokenViewKey,
            buttonLabel: msg("Copy token"),
            entityLabel: msg("Token"),
        });
    });
}
