/**
 * Display labels for the top-level documentation topics, used as the section
 * headings in the generated `llms.txt`. The keys are the top-level directory
 * slugs (and the `glossary` group split out of `core/glossary`); labels mirror
 * the site sidebar. Slugs without an entry fall back to a title-cased form.
 *
 * @type {ReadonlyArray<readonly [string, string]>}
 */
export default [
    ["index", "Overview"],
    ["core", "Core Concepts"],
    ["glossary", "Glossary"],
    ["add-secure-apps", "Add and Secure Applications"],
    ["customize", "Customize your Instance"],
    ["developer-docs", "Developer Documentation"],
    ["endpoint-devices", "Endpoint Devices"],
    ["enterprise", "Enterprise"],
    ["install-config", "Installation and Configuration"],
    ["security", "Security"],
    ["sys-mgmt", "System Management"],
    ["troubleshooting", "Troubleshooting"],
    ["users-sources", "Manage Users and Sources"],
];
