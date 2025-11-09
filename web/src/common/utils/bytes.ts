/**
 * Format bytes to a human-readable string
 *
 * @param bytes - Number of bytes
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string with appropriate unit (B, KB, MB, GB, TB)
 *
 * @example
 * formatBytes(1024) // "1 KB"
 * formatBytes(1234) // "1.21 KB"
 * formatBytes(1234567) // "1.18 MB"
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
    if (bytes === 0) return "0 B";

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const value = bytes / Math.pow(k, i);

    const rounded = Math.round(value * Math.pow(10, dm)) / Math.pow(10, dm);

    return `${rounded} ${sizes[i]}`;
}
