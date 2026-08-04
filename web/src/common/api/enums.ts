const UNKNOWN_DEFAULT_OPEN_API = "UnknownDefaultOpenApi";

type OpenAPIEnum = Readonly<Record<string, string | number | boolean>>;
type OpenAPIEnumKey<T extends OpenAPIEnum> = Exclude<
    Extract<keyof T, string>,
    typeof UNKNOWN_DEFAULT_OPEN_API
>;

export interface OpenAPIEnumOption<T extends OpenAPIEnum> {
    label: string;
    value: T[OpenAPIEnumKey<T>];
}

/** Prefer URI fragment labels (e.g. `#rsa-sha256` → `RSA-SHA256`), else the enum key. */
function openAPIEnumLabel(key: string, value: string | number | boolean): string {
    if (typeof value === "string") {
        const separator = value.lastIndexOf("#");
        if (separator >= 0 && separator < value.length - 1) {
            return value.slice(separator + 1).toUpperCase();
        }
    }
    return key;
}

/**
 * Convert a generated OpenAPI enum into UI options, omitting its unknown sentinel.
 *
 * Intended for choice sets whose UI labels do not need translation: vendor names
 * via `x-enum-varnames`, or algorithm URIs whose fragment is the display label.
 */
export function openAPIEnumOptions<T extends OpenAPIEnum>(enumValues: T): OpenAPIEnumOption<T>[] {
    return Object.keys(enumValues)
        .filter((key): key is OpenAPIEnumKey<T> => key !== UNKNOWN_DEFAULT_OPEN_API)
        .map((key) => {
            const value = enumValues[key];
            return {
                label: openAPIEnumLabel(key, value),
                value,
            };
        });
}
