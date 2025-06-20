import { usePluginData } from "@docusaurus/useGlobalData";
import { AKReleasesPluginData } from "@site/releases/plugin.mjs";
import { VersionDropdown } from "@site/src/components/VersionPicker/VersionDropdown";
import { useHostname, usePrereleaseOrigin } from "@site/src/components/VersionPicker/utils";

/**
 * A component that shows the available versions of the documentation.
 *
 * @see {@linkcode VersionPickerLoader} for the data-fetching component.
 */
export const VersionPicker: React.FC = () => {
    const hostname = useHostname();
    const prereleaseOrigin = usePrereleaseOrigin();

    const pluginData = usePluginData("ak-releases-plugin", undefined) as
        | AKReleasesPluginData
        | undefined;

    if (!pluginData?.releases.length) return null;

    // return <VersionPickerLoader pluginData={pluginData} />;

    return (
        <VersionDropdown
            hostname={hostname}
            prereleaseOrigin={prereleaseOrigin}
            releases={pluginData.releases}
        />
    );
};
