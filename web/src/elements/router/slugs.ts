/**
 * Given a string, return a URL-friendly slug.
 */
export function formatAsSlug(text: string): string {
    return text
        .toLowerCase()
        .replace(/ /g, "-")
        .replace(/[^\w-]+/g, "");
}

/**
 * Type guard to check if a given string is a valid URL slug, i.e.
 * only containing alphanumeric characters, dashes, and underscores.
 */
export function isSlug(input: unknown): input is string {
    if (typeof input !== "string") return false;
    if (!input) return false;

    const lowered = input.toLowerCase();
    if (input !== lowered) return false;

    return /([^\w-]|\s)/.test(lowered);
}
