/**
 * @typedef {object} GlobalAuthentik
 * @property {object} brand
 * @property {string} brand.branding_logo
 * @property {object} api
 * @property {string} api.base
 */

/**
 * Retrieves the global authentik object from the window.
 * @throws {Error} If the object not found
 * @returns {GlobalAuthentik}
 */
export function ak() {
    if (!("authentik" in window)) {
        throw new Error("No authentik object found in window");
    }

    return /** @type {GlobalAuthentik} */ (window.authentik);
}
