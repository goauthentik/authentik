/**
 * Accepted shapes for a JSX `class` prop, mirroring clsx: strings, numbers,
 * nullish/false/0/NaN (dropped), arrays of the same, and records whose truthy
 * keys are included.
 */
export type ClassValue =
    | string
    | number
    | null
    | undefined
    | false
    | readonly ClassValue[]
    | Record<string, unknown>;

export function normalizeClassValue(value: ClassValue): string {
    if (!value) {
        return "";
    }

    if (typeof value === "string" || typeof value === "number") {
        return String(value);
    }

    if (Array.isArray(value)) {
        return value.map(normalizeClassValue).filter(Boolean).join(" ");
    }

    return Object.entries(value)
        .filter(([, condition]) => Boolean(condition))
        .map(([className]) => className)
        .join(" ");
}
