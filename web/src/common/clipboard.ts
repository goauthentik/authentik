import { APIMessage, MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";

import { msg, str } from "@lit/localize";

function castToClipboardItem(input: string, mimeType = "text/plain"): ClipboardItem {
    return new ClipboardItem({
        [mimeType]: new Blob([input], {
            type: mimeType,
        }),
    });
}

export async function doWriteToClipboard(...data: string[] | ClipboardItem[]): Promise<void> {
    if (data.every((item) => typeof item === "string")) {
        return navigator.clipboard.write(data.map((item) => castToClipboardItem(item)));
    }

    return navigator.clipboard.write(data);
}

/**
 * Copies data to the clipboard.
 *
 * @param data The data to copy. Either a plain-text `string` or a {@linkcode ClipboardItem}.
 * @param entityLabel Localized label for the copied entity, used in success message.
 * @param description Optional description for the success message.
 *
 * @return A promise resolving to `true` on success, `false` on failure.
 */
export function writeToClipboard(
    data: string | ClipboardItem | string[] | ClipboardItem[] | null | undefined,
    entityLabel?: string,
    description?: string,
): Promise<boolean> {
    if (!data || (Array.isArray(data) && data.length === 0)) {
        console.warn("Cannot write empty data to clipboard");

        return Promise.resolve(false);
    }

    const normalized = typeof data === "string" ? castToClipboardItem(data) : data;

    return doWriteToClipboard(...(Array.isArray(normalized) ? normalized : [normalized]))
        .then(() => {
            const message: APIMessage = {
                level: MessageLevel.info,
                icon: "fas fa-clipboard-check",
                message: entityLabel
                    ? msg(str`${entityLabel} copied to clipboard.`, {
                          id: "clipboard.write.success.message.entity",
                      })
                    : msg("Copied to clipboard.", {
                          id: "clipboard.write.success.generic",
                      }),
                description,
            };

            showMessage(message, true);

            return true;
        })
        .catch((error) => {
            console.error("Failed to write to clipboard:", error);
            const fallbackDescription = msg(
                "Clipboard not available. Please copy the value manually.",
                {
                    id: "clipboard.write.failure.description",
                },
            );

            if (typeof data === "string") {
                showMessage(
                    {
                        level: MessageLevel.warning,
                        message: data,
                        description: fallbackDescription,
                    },
                    true,
                );
            } else {
                showMessage(
                    {
                        level: MessageLevel.warning,
                        message: fallbackDescription,
                    },
                    true,
                );
            }

            return false;
        });
}
