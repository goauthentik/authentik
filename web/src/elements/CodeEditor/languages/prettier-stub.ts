/**
 * @file Stands in for Prettier in the YAML worker, whose formatter the editor does not offer.
 */

export function format(): never {
    throw new Error("Formatting is not available in the code editor.");
}
