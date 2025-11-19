import { isSafari } from "./useragent.js";

export async function writeToClipboard(message: string) {
    if (!navigator.clipboard) {
        return false;
    }

    // Safari only allows navigator.clipboard.write with native clipboard items.
    try {
        if (isSafari()) {
            await navigator.clipboard.write([
                new ClipboardItem({
                    "text/plain": new Blob([message], {
                        type: "text/plain",
                    }),
                }),
            ]);
        } else {
            await navigator.clipboard.writeText(message);
        }
        return true;
    } catch (_) {
        /* no op */
    }
    return false;
}
