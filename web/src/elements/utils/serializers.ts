import type { Tagged } from "type-fest";

export type SerializedJSON<T = unknown> = Tagged<string, "JSON", T>;

export const serializeJSON = <T = unknown>(input: T, newline = true, space: string | number = 4) =>
    (JSON.stringify(input, null, space) + (newline ? "\n" : "")) as SerializedJSON<T>;
