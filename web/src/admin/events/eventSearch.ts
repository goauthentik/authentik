/**
 * DjangoQL search expression matching the given event uuids — an equality
 * check for one, an `in (...)` list for several.
 */
export function eventUuidSearch(ids: string[]): string {
    if (ids.length === 0) return "";
    if (ids.length === 1) return `event_uuid = "${ids[0]}"`;
    return `event_uuid in (${ids.map((id) => `"${id}"`).join(", ")})`;
}
