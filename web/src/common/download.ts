import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";

import { msg, str } from "@lit/localize";

// Download a file directly from the frontend. Must be called from a user-interaction event handler
// as this uses an <a> element behind the scenes.
export function downloadFile(content: string, filename: string, mime: string) {
    const blob = new Blob([content], { type: mime });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    showMessage({
        level: MessageLevel.info,
        message: msg(str`Successfully downloaded ${filename}!`),
    });
}
