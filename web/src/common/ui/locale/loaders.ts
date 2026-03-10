import { SourceLanguageTag } from "#common/ui/locale/definitions";
import { formatDisplayName } from "#common/ui/locale/format";

import { ConsoleLogger, Logger } from "#logger/browser";

import { LocaleModule, RuntimeConfiguration } from "@lit/localize";

/**
 * A record mapping locale codes to their respective module loaders.
 *
 * @remarks
 * The `import` statements **must** reference a locale module path,
 * as this is how ESBuild identifies which files to include in the build.
 */
export type LocaleLoaderRecord = Record<string, (() => Promise<LocaleModule>) | undefined>;

export interface LocaleLoaderInit {
    loaders?: LocaleLoaderRecord;
    sourceLocale?: string;
    logger?: Logger;
}

/**
 * A dummy locale module representing the source locale (English).
 *
 * @remarks
 * This is used to satisfy the return type of {@linkcode LocaleLoaderRecord}
 * for the source locale, which does not need to be loaded.
 */
const sourceTargetModule: LocaleModule = {
    templates: {},
};

export class LocaleLoader {
    public readonly loaders: LocaleLoaderRecord;
    public readonly sourceLocale: string;
    public readonly logger: Logger;

    constructor({ loaders, sourceLocale, logger }: LocaleLoaderInit = {}) {
        this.sourceLocale = sourceLocale || SourceLanguageTag;
        this.logger = logger ?? ConsoleLogger.prefix("LocaleLoader");
        this.loaders = {
            [SourceLanguageTag]: () => Promise.resolve(sourceTargetModule),
            ...loaders,
        };
    }

    /**
     * Loads the locale module for the given locale code.
     *
     * @param languageCode The language code to load.
     *
     * @remarks
     * This is used by `@lit/localize` to dynamically load locale modules,
     * as well synchronizing the document's `lang` attribute.
     */

    public load = async (
        languageCode: Intl.UnicodeBCP47LocaleIdentifier,
    ): Promise<LocaleModule> => {
        const languageNames = new Intl.DisplayNames([languageCode, this.sourceLocale], {
            type: "language",
        });

        const displayName = formatDisplayName(languageCode, languageCode, languageNames);
        const loader = this.loaders[languageCode];

        if (!loader) {
            // Lit localize ensures this function is only called with valid locales
            // but we add a runtime check nonetheless.

            throw new TypeError(`Unsupported language code: ${languageCode} (${displayName})`);
        }

        this.logger.debug(`Loading "${displayName}" module...`);

        return loader();
    };

    public toRuntimeConfig(): RuntimeConfiguration {
        return {
            loadLocale: this.load,
            sourceLocale: this.sourceLocale,
            targetLocales: Object.keys(this.loaders),
        };
    }
}
