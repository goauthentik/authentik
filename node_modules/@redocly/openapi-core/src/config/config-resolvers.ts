import * as path from 'path';
import { isAbsoluteUrl } from '../ref-utils';
import { pickDefined } from '../utils';
import { resolveDocument, BaseResolver } from '../resolve';
import { defaultPlugin } from './builtIn';
import {
  getResolveConfig,
  getUniquePlugins,
  mergeExtends,
  parsePresetName,
  prefixRules,
  transformConfig,
} from './utils';
import { isBrowser } from '../env';
import { isNotString, isString, isDefined, keysOf } from '../utils';
import { Config } from './config';
import { colorize, logger } from '../logger';
import { asserts, buildAssertCustomFunction } from '../rules/common/assertions/asserts';
import { normalizeTypes } from '../types';
import { ConfigTypes } from '../types/redocly-yaml';

import type {
  StyleguideRawConfig,
  ApiStyleguideRawConfig,
  Plugin,
  RawConfig,
  ResolvedApi,
  ResolvedStyleguideConfig,
  RuleConfig,
  DeprecatedInRawConfig,
} from './types';
import type { Assertion, AssertionDefinition, RawAssertion } from '../rules/common/assertions';
import type { Asserts, AssertionFn } from '../rules/common/assertions/asserts';
import type { BundleOptions } from '../bundle';
import type { Document, ResolvedRefMap } from '../resolve';

export async function resolveConfigFileAndRefs({
  configPath,
  externalRefResolver = new BaseResolver(),
  base = null,
}: Omit<BundleOptions, 'config'> & { configPath?: string }): Promise<{
  document: Document;
  resolvedRefMap: ResolvedRefMap;
}> {
  if (!configPath) {
    throw new Error('Reference to a config is required.\n');
  }

  const document = await externalRefResolver.resolveDocument(base, configPath, true);

  if (document instanceof Error) {
    throw document;
  }

  const types = normalizeTypes(ConfigTypes);

  const resolvedRefMap = await resolveDocument({
    rootDocument: document,
    rootType: types.ConfigRoot,
    externalRefResolver,
  });

  return { document, resolvedRefMap };
}

export async function resolveConfig({
  rawConfig,
  configPath,
  externalRefResolver,
}: {
  rawConfig: RawConfig;
  configPath?: string;
  externalRefResolver?: BaseResolver;
}): Promise<Config> {
  if (rawConfig.styleguide?.extends?.some(isNotString)) {
    throw new Error(
      `Error configuration format not detected in extends value must contain strings`
    );
  }

  const resolver = externalRefResolver ?? new BaseResolver(getResolveConfig(rawConfig.resolve));

  const apis = await resolveApis({
    rawConfig,
    configPath,
    resolver,
  });

  const styleguide = await resolveStyleguideConfig({
    styleguideConfig: rawConfig.styleguide,
    configPath,
    resolver,
  });

  return new Config(
    {
      ...rawConfig,
      apis,
      styleguide,
    },
    configPath
  );
}

export function resolvePlugins(
  plugins: (string | Plugin)[] | null,
  configPath: string = ''
): Plugin[] {
  if (!plugins) return [];

  // TODO: implement or reuse Resolver approach so it will work in node and browser envs
  const requireFunc = (plugin: string | Plugin): Plugin | undefined => {
    if (isBrowser && isString(plugin)) {
      logger.error(`Cannot load ${plugin}. Plugins aren't supported in browser yet.`);

      return undefined;
    }

    if (isString(plugin)) {
      try {
        const absoltePluginPath = path.resolve(path.dirname(configPath), plugin);
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        return typeof __webpack_require__ === 'function'
          ? // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            __non_webpack_require__(absoltePluginPath)
          : require(absoltePluginPath);
      } catch (e) {
        if (e instanceof SyntaxError) {
          throw e;
        }
        throw new Error(`Failed to load plugin "${plugin}". Please provide a valid path`);
      }
    }

    return plugin;
  };

  const seenPluginIds = new Map<string, string>();

  return plugins
    .map((p) => {
      if (isString(p) && isAbsoluteUrl(p)) {
        throw new Error(colorize.red(`We don't support remote plugins yet.`));
      }

      // TODO: resolve npm packages similar to eslint
      const pluginModule = requireFunc(p);

      if (!pluginModule) {
        return;
      }

      const id = pluginModule.id;
      if (typeof id !== 'string') {
        throw new Error(
          colorize.red(`Plugin must define \`id\` property in ${colorize.blue(p.toString())}.`)
        );
      }

      if (seenPluginIds.has(id)) {
        const pluginPath = seenPluginIds.get(id)!;
        throw new Error(
          colorize.red(
            `Plugin "id" must be unique. Plugin ${colorize.blue(
              p.toString()
            )} uses id "${colorize.blue(id)}" already seen in ${colorize.blue(pluginPath)}`
          )
        );
      }

      seenPluginIds.set(id, p.toString());

      const plugin: Plugin = {
        id,
        ...(pluginModule.configs ? { configs: pluginModule.configs } : {}),
        ...(pluginModule.typeExtension ? { typeExtension: pluginModule.typeExtension } : {}),
      };

      if (pluginModule.rules) {
        if (!pluginModule.rules.oas3 && !pluginModule.rules.oas2 && !pluginModule.rules.async2) {
          throw new Error(`Plugin rules must have \`oas3\`, \`oas2\` or \`async2\` rules "${p}.`);
        }
        plugin.rules = {};
        if (pluginModule.rules.oas3) {
          plugin.rules.oas3 = prefixRules(pluginModule.rules.oas3, id);
        }
        if (pluginModule.rules.oas2) {
          plugin.rules.oas2 = prefixRules(pluginModule.rules.oas2, id);
        }
        if (pluginModule.rules.async2) {
          plugin.rules.async2 = prefixRules(pluginModule.rules.async2, id);
        }
      }
      if (pluginModule.preprocessors) {
        if (
          !pluginModule.preprocessors.oas3 &&
          !pluginModule.preprocessors.oas2 &&
          !pluginModule.preprocessors.async2
        ) {
          throw new Error(
            `Plugin \`preprocessors\` must have \`oas3\`, \`oas2\` or \`async2\` preprocessors "${p}.`
          );
        }
        plugin.preprocessors = {};
        if (pluginModule.preprocessors.oas3) {
          plugin.preprocessors.oas3 = prefixRules(pluginModule.preprocessors.oas3, id);
        }
        if (pluginModule.preprocessors.oas2) {
          plugin.preprocessors.oas2 = prefixRules(pluginModule.preprocessors.oas2, id);
        }
        if (pluginModule.preprocessors.async2) {
          plugin.preprocessors.async2 = prefixRules(pluginModule.preprocessors.async2, id);
        }
      }

      if (pluginModule.decorators) {
        if (
          !pluginModule.decorators.oas3 &&
          !pluginModule.decorators.oas2 &&
          !pluginModule.decorators.async2
        ) {
          throw new Error(
            `Plugin \`decorators\` must have \`oas3\`, \`oas2\` or \`async2\` decorators "${p}.`
          );
        }
        plugin.decorators = {};
        if (pluginModule.decorators.oas3) {
          plugin.decorators.oas3 = prefixRules(pluginModule.decorators.oas3, id);
        }
        if (pluginModule.decorators.oas2) {
          plugin.decorators.oas2 = prefixRules(pluginModule.decorators.oas2, id);
        }
        if (pluginModule.decorators.async2) {
          plugin.decorators.async2 = prefixRules(pluginModule.decorators.async2, id);
        }
      }

      if (pluginModule.assertions) {
        plugin.assertions = pluginModule.assertions;
      }

      return plugin;
    })
    .filter(isDefined);
}

export async function resolveApis({
  rawConfig,
  configPath = '',
  resolver,
}: {
  rawConfig: RawConfig;
  configPath?: string;
  resolver?: BaseResolver;
}): Promise<Record<string, ResolvedApi>> {
  const { apis = {}, styleguide: styleguideConfig = {} } = rawConfig;
  const resolvedApis: Record<string, ResolvedApi> = {};
  for (const [apiName, apiContent] of Object.entries(apis || {})) {
    if (apiContent.styleguide?.extends?.some(isNotString)) {
      throw new Error(
        `Error configuration format not detected in extends value must contain strings`
      );
    }
    const rawStyleguideConfig = getMergedRawStyleguideConfig(
      styleguideConfig,
      apiContent.styleguide
    );
    const resolvedApiConfig = await resolveStyleguideConfig({
      styleguideConfig: rawStyleguideConfig,
      configPath,
      resolver,
    });
    resolvedApis[apiName] = { ...apiContent, styleguide: resolvedApiConfig };
  }
  return resolvedApis;
}

async function resolveAndMergeNestedStyleguideConfig(
  {
    styleguideConfig,
    configPath = '',
    resolver = new BaseResolver(),
  }: {
    styleguideConfig?: StyleguideRawConfig;
    configPath?: string;
    resolver?: BaseResolver;
  },
  parentConfigPaths: string[] = [],
  extendPaths: string[] = []
): Promise<ResolvedStyleguideConfig> {
  if (parentConfigPaths.includes(configPath)) {
    throw new Error(`Circular dependency in config file: "${configPath}"`);
  }
  const plugins = getUniquePlugins(
    resolvePlugins([...(styleguideConfig?.plugins || []), defaultPlugin], configPath)
  );
  const pluginPaths = styleguideConfig?.plugins
    ?.filter(isString)
    .map((p) => path.resolve(path.dirname(configPath), p));

  const resolvedConfigPath = isAbsoluteUrl(configPath)
    ? configPath
    : configPath && path.resolve(configPath);

  const extendConfigs: ResolvedStyleguideConfig[] = await Promise.all(
    styleguideConfig?.extends?.map(async (presetItem) => {
      if (!isAbsoluteUrl(presetItem) && !path.extname(presetItem)) {
        return resolvePreset(presetItem, plugins);
      }
      const pathItem = isAbsoluteUrl(presetItem)
        ? presetItem
        : isAbsoluteUrl(configPath)
        ? new URL(presetItem, configPath).href
        : path.resolve(path.dirname(configPath), presetItem);
      const extendedStyleguideConfig = await loadExtendStyleguideConfig(pathItem, resolver);
      return await resolveAndMergeNestedStyleguideConfig(
        {
          styleguideConfig: extendedStyleguideConfig,
          configPath: pathItem,
          resolver: resolver,
        },
        [...parentConfigPaths, resolvedConfigPath],
        extendPaths
      );
    }) || []
  );

  const { plugins: mergedPlugins = [], ...styleguide } = mergeExtends([
    ...extendConfigs,
    {
      ...styleguideConfig,
      plugins,
      extends: undefined,
      extendPaths: [...parentConfigPaths, resolvedConfigPath],
      pluginPaths,
    },
  ]);

  return {
    ...styleguide,
    extendPaths: styleguide.extendPaths?.filter((path) => path && !isAbsoluteUrl(path)),
    plugins: getUniquePlugins(mergedPlugins),
    recommendedFallback: styleguideConfig?.recommendedFallback,
    doNotResolveExamples: styleguideConfig?.doNotResolveExamples,
  };
}

export async function resolveStyleguideConfig(
  opts: {
    styleguideConfig?: StyleguideRawConfig;
    configPath?: string;
    resolver?: BaseResolver;
  },
  parentConfigPaths: string[] = [],
  extendPaths: string[] = []
): Promise<ResolvedStyleguideConfig> {
  const resolvedStyleguideConfig = await resolveAndMergeNestedStyleguideConfig(
    opts,
    parentConfigPaths,
    extendPaths
  );

  return {
    ...resolvedStyleguideConfig,
    rules:
      resolvedStyleguideConfig.rules && groupStyleguideAssertionRules(resolvedStyleguideConfig),
  };
}

export function resolvePreset(presetName: string, plugins: Plugin[]): ResolvedStyleguideConfig {
  const { pluginId, configName } = parsePresetName(presetName);
  const plugin = plugins.find((p) => p.id === pluginId);
  if (!plugin) {
    throw new Error(
      `Invalid config ${colorize.red(presetName)}: plugin ${pluginId} is not included.`
    );
  }

  const preset = plugin.configs?.[configName];
  if (!preset) {
    throw new Error(
      pluginId
        ? `Invalid config ${colorize.red(
            presetName
          )}: plugin ${pluginId} doesn't export config with name ${configName}.`
        : `Invalid config ${colorize.red(presetName)}: there is no such built-in config.`
    );
  }
  return preset;
}

async function loadExtendStyleguideConfig(
  filePath: string,
  resolver: BaseResolver
): Promise<StyleguideRawConfig> {
  try {
    const { parsed } = (await resolver.resolveDocument(null, filePath)) as Document;
    const rawConfig = transformConfig(parsed as RawConfig & DeprecatedInRawConfig);
    if (!rawConfig.styleguide) {
      throw new Error(`Styleguide configuration format not detected: "${filePath}"`);
    }

    return rawConfig.styleguide;
  } catch (error) {
    throw new Error(`Failed to load "${filePath}": ${error.message}`);
  }
}

function getMergedRawStyleguideConfig(
  rootStyleguideConfig: StyleguideRawConfig,
  apiStyleguideConfig?: ApiStyleguideRawConfig
) {
  const resultLint = {
    ...rootStyleguideConfig,
    ...pickDefined(apiStyleguideConfig),
    rules: { ...rootStyleguideConfig?.rules, ...apiStyleguideConfig?.rules },
    oas2Rules: { ...rootStyleguideConfig?.oas2Rules, ...apiStyleguideConfig?.oas2Rules },
    oas3_0Rules: { ...rootStyleguideConfig?.oas3_0Rules, ...apiStyleguideConfig?.oas3_0Rules },
    oas3_1Rules: { ...rootStyleguideConfig?.oas3_1Rules, ...apiStyleguideConfig?.oas3_1Rules },
    preprocessors: {
      ...rootStyleguideConfig?.preprocessors,
      ...apiStyleguideConfig?.preprocessors,
    },
    oas2Preprocessors: {
      ...rootStyleguideConfig?.oas2Preprocessors,
      ...apiStyleguideConfig?.oas2Preprocessors,
    },
    oas3_0Preprocessors: {
      ...rootStyleguideConfig?.oas3_0Preprocessors,
      ...apiStyleguideConfig?.oas3_0Preprocessors,
    },
    oas3_1Preprocessors: {
      ...rootStyleguideConfig?.oas3_1Preprocessors,
      ...apiStyleguideConfig?.oas3_1Preprocessors,
    },
    decorators: { ...rootStyleguideConfig?.decorators, ...apiStyleguideConfig?.decorators },
    oas2Decorators: {
      ...rootStyleguideConfig?.oas2Decorators,
      ...apiStyleguideConfig?.oas2Decorators,
    },
    oas3_0Decorators: {
      ...rootStyleguideConfig?.oas3_0Decorators,
      ...apiStyleguideConfig?.oas3_0Decorators,
    },
    oas3_1Decorators: {
      ...rootStyleguideConfig?.oas3_1Decorators,
      ...apiStyleguideConfig?.oas3_1Decorators,
    },
    recommendedFallback: apiStyleguideConfig?.extends
      ? false
      : rootStyleguideConfig.recommendedFallback,
  };
  return resultLint;
}

function groupStyleguideAssertionRules({
  rules,
  plugins,
}: ResolvedStyleguideConfig): Record<string, RuleConfig> | undefined {
  if (!rules) {
    return rules;
  }

  // Create a new record to avoid mutating original
  const transformedRules: Record<string, RuleConfig> = {};

  // Collect assertion rules
  const assertions: Assertion[] = [];
  for (const [ruleKey, rule] of Object.entries(rules)) {
    // keep the old assert/ syntax as an alias

    if (
      (ruleKey.startsWith('rule/') || ruleKey.startsWith('assert/')) &&
      typeof rule === 'object' &&
      rule !== null
    ) {
      const assertion = rule as RawAssertion;

      if (plugins) {
        registerCustomAssertions(plugins, assertion);

        // We may have custom assertion inside where block
        for (const context of assertion.where || []) {
          registerCustomAssertions(plugins, context);
        }
      }
      assertions.push({
        ...assertion,
        assertionId: ruleKey,
      });
    } else {
      // If it's not an assertion, keep it as is
      transformedRules[ruleKey] = rule;
    }
  }
  if (assertions.length > 0) {
    transformedRules.assertions = assertions;
  }

  return transformedRules;
}

function registerCustomAssertions(plugins: Plugin[], assertion: AssertionDefinition) {
  for (const field of keysOf(assertion.assertions)) {
    const [pluginId, fn] = field.split('/');

    if (!pluginId || !fn) continue;

    const plugin = plugins.find((plugin) => plugin.id === pluginId);

    if (!plugin) {
      throw Error(colorize.red(`Plugin ${colorize.blue(pluginId)} isn't found.`));
    }

    if (!plugin.assertions || !plugin.assertions[fn]) {
      throw Error(
        `Plugin ${colorize.red(
          pluginId
        )} doesn't export assertions function with name ${colorize.red(fn)}.`
      );
    }

    (asserts as Asserts & { [name: string]: AssertionFn })[field] = buildAssertCustomFunction(
      plugin.assertions[fn]
    );
  }
}
