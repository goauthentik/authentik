import { type OpenAPIEnum, OpenAPIEnumLabels } from "@goauthentik/api";

const UNKNOWN_DEFAULT_OPEN_API = "UnknownDefaultOpenApi";
type OpenAPIEnumKey<T extends OpenAPIEnum> = Exclude<
    Extract<keyof T, string>,
    typeof UNKNOWN_DEFAULT_OPEN_API
>;

export interface OpenAPIEnumOption<T extends OpenAPIEnum> {
    label: string;
    value: T[OpenAPIEnumKey<T>];
}

/** Convert a generated OpenAPI enum into UI options, omitting its unknown sentinel. */
export function openAPIEnumOptions<T extends OpenAPIEnum>(enumValues: T): OpenAPIEnumOption<T>[] {
    const labels = OpenAPIEnumLabels.get(enumValues);
    return Object.keys(enumValues)
        .filter((key): key is OpenAPIEnumKey<T> => key !== UNKNOWN_DEFAULT_OPEN_API)
        .map((key, index) => {
            const value = enumValues[key];
            const label =
                labels && labels.length > index ? labels[index] : key;
            return {
                label,
                value,
            };
        });
}
