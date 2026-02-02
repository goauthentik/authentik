/**
 * @file Download utility functions.
 */

export interface DownloadInit extends BlobPropertyBag {
    content: BlobPart | BlobPart[];
    filename: string;
}

/**
 * Download a file directly from the frontend.
 *
 * @remarks
 * This function must be called from a user-interaction event handler
 * as it uses an `<a>` element behind the scenes.
 */
export function downloadFile({ content, filename, ...options }: DownloadInit): void {
    const blob = new Blob(Array.isArray(content) ? content : [content], options);

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);

    a.click();

    URL.revokeObjectURL(url);
    document.body.removeChild(a);
}
