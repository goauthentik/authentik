import { MessageLevel } from "#common/messages";
import { isPromiseLike } from "#common/promises";

import { showMessage } from "#elements/messages/MessageContainer";

import { msg, str } from "@lit/localize";

export type ClipboardItemSource = string | ClipboardItemData | ClipboardItem;

/**
 * Helper function to convert a string into a ClipboardItem for writing to the clipboard.
 *
 * @remarks
 * This requires either a secure context (HTTPS) or localhost.
 */
function castToClipboardItem(source: ClipboardItemSource, mimeType = "text/plain"): ClipboardItem {
    if (source instanceof ClipboardItem) {
        return source;
    }

    const data = typeof source === "string" ? new Blob([source], { type: mimeType }) : source;

    return new ClipboardItem({
        [mimeType]: data,
    });
}

/**
 * Writes data to the clipboard using the Clipboard API.
 *
 * @remarks
 * This requires either a secure context (HTTPS) or localhost.
 */
export async function doWriteToClipboard(...data: ClipboardItemSource[]): Promise<void> {
    return navigator.clipboard.write(data.map((item) => castToClipboardItem(item)));
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
    data?: ClipboardItemSource | ClipboardItemSource[] | null,
    entityLabel?: string,
    description?: string,
): Promise<boolean> {
    if (!data || (Array.isArray(data) && data.length === 0)) {
        console.warn("Cannot write empty data to clipboard");

        return Promise.resolve(false);
    }
    const messageKey = `clipboard-success-${entityLabel ?? "generic"}`;

    // Wrap with promise to simplify fallback behavior.
    const clipboardItemsPromise = new Promise<ClipboardItemSource[]>((resolve) => {
        const hasAsyncData = Array.isArray(data) ? data.some(isPromiseLike) : isPromiseLike(data);

        if (hasAsyncData) {
            showMessage({
                level: MessageLevel.info,
                icon: "fas fa-clipboard-check",
                message: entityLabel
                    ? msg(str`Copying ${entityLabel}...`, {
                          id: "clipboard.progress.message.entity",
                      })
                    : msg("Copying to clipboard...", {
                          id: "clipboard.progress.generic",
                      }),
                description,
                key: messageKey,
            });
        }

        const normalized = typeof data === "string" ? castToClipboardItem(data) : data;
        const items = Array.isArray(normalized) ? normalized : [normalized];

        resolve(items);
    });

    return clipboardItemsPromise
        .then((items) => doWriteToClipboard(...items))
        .then(() => {
            showMessage({
                level: MessageLevel.success,
                icon: "fas fa-clipboard-check",
                message: entityLabel
                    ? msg(str`${entityLabel} copied to clipboard.`, {
                          id: "clipboard.write.success.message.entity",
                      })
                    : msg("Copied to clipboard.", {
                          id: "clipboard.write.success.generic",
                      }),
                description,
                key: messageKey,
            });

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
