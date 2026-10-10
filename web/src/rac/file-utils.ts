/** Keep this basename policy aligned with the RAC backend. */
export function sanitizeFilename(value: string): string {
    // Control characters must be removed before constructing a remote filename.
    let name = value.replace(/[\\/\p{Cc}\p{Cf}<>:"|?*]/gu, "_").replace(/^[ .]+|[ .]+$/g, "");
    const encoder = new TextEncoder();

    while (encoder.encode(name).length > 200) {
        name = Array.from(name).slice(0, -1).join("");
    }

    return name.replace(/^[ .]+|[ .]+$/g, "") || "download";
}

export const UPLOAD_CHUNK_SIZE = 4 * 1024 * 1024;
