/**
 * @license MIT
 * @file Vendored DOMException for Node.js environments.
 * @author Jimmy Wärting
 * @see https://github.com/jimmywarting/node-domexception
 */

globalThis.DOMException ??= (() => {
    try {
        // @ts-expect-error Trigger a DOMException to get its constructor.
        atob(0);
    } catch (err) {
        // @ts-expect-error unknown type
        return err.constructor;
    }
})();
