/**
 * @file Search-parameter serialization for path-based routing.
 *
 * Round-trips primitive route parameters (string, number, boolean, and arrays
 * thereof) to and from `URLSearchParams`. App-context-free.
 *
 * Adapted from the `basepath-aware-routing` prototype's `parsing.ts`.
 */

export type PrimitiveRouteParameter = string | number | boolean | null | undefined;

export type RouteParameterRecord = Record<
    string,
    PrimitiveRouteParameter | PrimitiveRouteParameter[]
>;

export type RouterParameterInit = RouteParameterRecord | URLSearchParams;

/**
 * Serialize a single primitive to a search-param string, or `null` to omit it.
 *
 * Empty, nullish, and `false` values are omitted; `true` becomes `"true"`.
 */
function serialize(value: PrimitiveRouteParameter): string | null {
    if (value === null || value === undefined || value === "") return null;

    if (typeof value === "boolean") {
        return value ? "true" : null;
    }

    return value.toString();
}

/**
 * Given a record of parameters, build a `URLSearchParams` object.
 *
 * A `URLSearchParams` input is returned as-is.
 */
export function recordToSearchParams(params: RouterParameterInit): URLSearchParams {
    if (params instanceof URLSearchParams) {
        return params;
    }

    const searchParams = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        if (Array.isArray(value)) {
            for (const item of value) {
                const serialized = serialize(item);

                if (serialized === null) continue;

                searchParams.append(key, serialized);
            }

            continue;
        }

        const serialized = serialize(value);

        if (serialized === null) continue;

        searchParams.set(key, serialized);
    }

    return searchParams;
}

/**
 * Deserialize a single search-param string back to a primitive.
 */
function deserialize(value: string): PrimitiveRouteParameter {
    if (value === "true") return true;
    if (value === "false") return false;

    if (/^\d+$/.test(value)) {
        const parsed = Number(value);

        if (Number.isSafeInteger(parsed) && String(parsed) === value) {
            return parsed;
        }
    }

    return value;
}

/**
 * Given a `URLSearchParams` object, build a record of parameters.
 *
 * Keys that appear multiple times are collected into an array of values.
 */
export function searchParamsToRecord<T extends RouteParameterRecord = RouteParameterRecord>(
    searchParams: URLSearchParams,
): T {
    const params: Record<string, PrimitiveRouteParameter | PrimitiveRouteParameter[]> = {};

    for (const [key, raw] of searchParams.entries()) {
        const value = deserialize(raw);
        const existing = params[key];

        if (existing === undefined) {
            params[key] = value;
        } else if (Array.isArray(existing)) {
            existing.push(value);
        } else {
            params[key] = [existing, value];
        }
    }

    return params as T;
}
