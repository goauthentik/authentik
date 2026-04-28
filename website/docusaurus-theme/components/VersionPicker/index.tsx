import { useVersionPluginData } from "#components/VersionPicker/utils.ts";
import { VersionPickerLoader } from "#components/VersionPicker/VersionPickerLoader.tsx";

/**
 * A component that shows the available versions of the documentation.
 *
 * @see {@linkcode VersionPickerLoader} for the data-fetching component.
 */
export const VersionPicker: React.FC = () => {
    const pluginData = useVersionPluginData();

    if (!pluginData) return null;

    return <VersionPickerLoader pluginData={pluginData} />;
};
