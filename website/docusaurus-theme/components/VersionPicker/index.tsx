import { useHostname } from "#components/VersionPicker/utils.ts";
import { VersionDropdown } from "#components/VersionPicker/VersionDropdown.tsx";

import { AKReleasesPluginData } from "@goauthentik/docusaurus-theme/releases/plugin";

import { usePluginData } from "@docusaurus/useGlobalData";

/**
 * A component that shows the available versions of the documentation.
 *
 * @see {@linkcode VersionPickerLoader} for the data-fetching component.
 */
export const VersionPicker: React.FC = () => {
    const hostname = useHostname();

    const pluginData = usePluginData("ak-releases-plugin", undefined) as
        | AKReleasesPluginData
        | undefined;

    if (!pluginData?.releases.length) return null;

    // return <VersionPickerLoader pluginData={pluginData} />;

    return (
        <VersionDropdown
            hostname={hostname}
            releases={pluginData.releases}
            branch={pluginData.branch}
        />
    );
};
