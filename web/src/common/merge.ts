/** Taken from: https://github.com/zellwk/javascript/tree/master
 *
 * We have added some typescript annotations, but this is such a rich feature with deep nesting
 * we'll just have to watch it closely for any issues. So far there don't seem to be any.
 *
 */

function objectType<T>(value: T) {
    return Object.prototype.toString.call(value);
}

// Creates a deep clone for each value
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function cloneDescriptorValue(value: any) {
    // Arrays
    if (objectType(value) === "[object Array]") {
        const array = [];
        for (let v of value) {
            v = cloneDescriptorValue(v);
            array.push(v);
        }
        return array;
    }

    // Objects
    if (objectType(value) === "[object Object]") {
        const obj = {};
        const props = Object.keys(value);
        for (const prop of props) {
            const descriptor = Object.getOwnPropertyDescriptor(value, prop);
            if (!descriptor) {
                continue;
            }

            if (descriptor.value) {
                descriptor.value = cloneDescriptorValue(descriptor.value);
            }
            Object.defineProperty(obj, prop, descriptor);
        }
        return obj;
    }

    // Other Types of Objects
    if (objectType(value) === "[object Date]") {
        return new Date(value.getTime());
    }

    if (objectType(value) === "[object Map]") {
        const map = new Map();
        for (const entry of value) {
            map.set(entry[0], cloneDescriptorValue(entry[1]));
        }
        return map;
    }

    if (objectType(value) === "[object Set]") {
        const set = new Set();
        for (const entry of value.entries()) {
            set.add(cloneDescriptorValue(entry[0]));
        }
        return set;
    }

    // Types we don't need to clone or cannot clone.
    // Examples:
    // - Primitives don't need to clone
    // - Functions cannot clone
    return value;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function _merge(output: Record<string, any>, input: Record<string, any>) {
    const props = Object.keys(input);

    for (const prop of props) {
        // Prevents Prototype Pollution
        if (prop === "__proto__") continue;

        const descriptor = Object.getOwnPropertyDescriptor(input, prop);
        if (!descriptor) {
            continue;
        }

        const value = descriptor.value;
        if (value) descriptor.value = cloneDescriptorValue(value);

        // If don't have prop => Define property
        // [ken@goauthentik] Using `hasOwn` is preferable over
        // the basic identity test, according to Typescript.
        if (!Object.hasOwn(output, prop)) {
            Object.defineProperty(output, prop, descriptor);
            continue;
        }

        // If have prop, but type is not object => Overwrite by redefining property
        if (typeof output[prop] !== "object") {
            Object.defineProperty(output, prop, descriptor);
            continue;
        }

        // If have prop, but type is Object => Concat the arrays together.
        if (objectType(descriptor.value) === "[object Array]") {
            output[prop] = output[prop].concat(descriptor.value);
            continue;
        }

        // If have prop, but type is Object => Merge.
        _merge(output[prop], descriptor.value);
    }
}

export function merge(...sources: Array<object>) {
    const result = {};
    for (const source of sources) {
        _merge(result, source);
    }
    return result;
}

export default merge;
