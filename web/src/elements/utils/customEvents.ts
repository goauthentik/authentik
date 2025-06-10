export const customEvent = (name: string, details = {}) =>
    new CustomEvent(name as string, {
        composed: true,
        bubbles: true,
        detail: details,
    });

export type SerializablePrimitive = number | string;
export type SerializableArray = SerializablePrimitive[];
export type CustomEventDetail = SerializablePrimitive | SerializableArray | object;

/**
 * Type guard to determine if an event has a `detail` property.
 */
export function isCustomEvent<D = CustomEventDetail>(
    eventLike: Event,
): eventLike is CustomEvent<D> {
    return eventLike instanceof CustomEvent && "detail" in eventLike;
}
