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

/**
 * Convert a generated OpenAPI enum into UI options, omitting its unknown sentinel.
 *
 * Labels come from the generated enum member names (`x-enum-varnames`), so this
 * only fits choice sets whose names are already UI-safe (vendor names, SHA*, …).
 */
export function openAPIEnumOptions<T extends OpenAPIEnum>(enumValues: T): OpenAPIEnumOption<T>[] {
    return Object.keys(enumValues)
        .filter((key): key is OpenAPIEnumKey<T> => key !== UNKNOWN_DEFAULT_OPEN_API)
        .map((key) => ({
            label: key,
            value: enumValues[key],
        }));
}
