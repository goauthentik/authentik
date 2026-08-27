/**
 * @type {import('@docusaurus/types').DocusaurusConfig}
 */
module.exports = import("./docusaurus.config.esm.mjs").then(($) => $.default);
