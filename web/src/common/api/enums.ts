const UNKNOWN_DEFAULT_OPEN_API = "UnknownDefaultOpenApi";

type OpenAPIEnum = Readonly<Record<string, string>>;
type OpenAPIEnumKey<T extends OpenAPIEnum> = Exclude<
    Extract<keyof T, string>,
    typeof UNKNOWN_DEFAULT_OPEN_API
>;

/**
 * Convert a generated OpenAPI enum into UI options, omitting its unknown sentinel.
 *
 * Labels come from the member name, which the schema pins via `x-enum-varnames`, or from
 * the fragment of a URI value (`...#rsa-sha256` → `RSA-SHA256`). Neither is translated.
 */
export function openAPIEnumOptions<T extends OpenAPIEnum>(
    enumValues: T,
    defaultValue?: T[OpenAPIEnumKey<T>],
) {
    return Object.keys(enumValues)
        .filter((key): key is OpenAPIEnumKey<T> => key !== UNKNOWN_DEFAULT_OPEN_API)
        .map((key) => {
            const value = enumValues[key];
            return {
                label: value.split("#")[1]?.toUpperCase() || key,
                value,
                default: value === defaultValue,
            };
        });
}
