// Automatically binds a method to the `this` instance during instantiation.
// Uses the Typescript Experimental Decorator syntax, so we may be living with
// that for a long time.

// MDN is *not* very helpful. The type for a PropertyDescriptor is kept in
// typescript/lib/lib.es5.d.ts, but the description of what everything in
// a descriptor does isn't specified in MDN in its own page, only in
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty

// This decorator feels awkward. It gets a new instance of the method every time
// you reference the field. I wonder if there would be a way to create a lookup
// table; once you'd bound the method you could reuse that bound method for that
// instance, instead of throwing it away?

export function bound(
    target: unknown,
    key: string,
    descriptor: PropertyDescriptor,
): PropertyDescriptor {
    if (typeof descriptor?.value !== "function") {
        throw new Error("Only methods can be @bound.");
    }
    return {
        configurable: true,
        get() {
            const method = descriptor.value.bind(this);
            Object.defineProperty(this, key, { value: method, configurable: true, writable: true });
            return method;
        },
    };
}
