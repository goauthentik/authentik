import fs from 'fs';
import path from 'path';
import type {
  LoadContext,
  Plugin,
  OptionValidationContext,
} from '@docusaurus/types';
import { normalizeUrl } from '@docusaurus/utils';
import { loadAndBundleSpec } from 'redoc';
import type { OpenAPISpec } from 'redoc/typings/types';
import {
  formatProblems,
  getTotals,
  bundle,
  stringifyYaml,
  Document,
  NormalizedProblem,
} from '@redocly/openapi-core';

import {
  PluginOptionSchema,
  PluginOptions,
  PluginOptionsWithDefault,
  PluginDirectUsageOptions,
  DEFAULT_OPTIONS,
} from './options';
import type { SpecProps, ApiDocProps } from './types/common';
import { loadSpecWithConfig } from './loadSpec';
import { loadRedoclyConfig } from './loadRedoclyConfig';

// eslint-disable-next-line @typescript-eslint/no-var-requires
const version = require('../package.json').version;

export { PluginOptions, PluginDirectUsageOptions, loadRedoclyConfig };

export default function redocPlugin(
  context: LoadContext,
  opts: PluginOptions,
): Plugin<{
  converted: OpenAPISpec;
  bundle?: Record<string, unknown>;
}> {
  const { baseUrl } = context.siteConfig;
  const options: PluginOptionsWithDefault = { ...DEFAULT_OPTIONS, ...opts };
  const { debug, spec, url: downloadUrl, config, themeId } = options;

  let url = downloadUrl;
  const isSpecFile = fs.existsSync(spec);
  const fileName = path.join(
    'redocusaurus',
    `${options.id || 'api-spec'}.yaml`,
  );
  let filesToWatch: string[] = isSpecFile ? [path.resolve(spec)] : [];

  if (debug) {
    console.error('[REDOCUSAURUS_PLUGIN] Opts Input:', opts);
    console.error('[REDOCUSAURUS_PLUGIN] Options:', options);
  }

  return {
    name: 'docusaurus-plugin-redoc',
    async loadContent() {
      const redoclyConfig = await loadRedoclyConfig(config);
      if (redoclyConfig.configFile) {
        filesToWatch.push(redoclyConfig.configFile);
      }

      let bundledSpec: Document, problems: NormalizedProblem[];

      if (!isSpecFile) {
        // If spec is a remote url then add it as download url also as a default
        url = url || spec;
        if (debug) {
          console.log('[REDOCUSAURUS_PLUGIN] bundling spec from url', spec);
        }
        ({ bundle: bundledSpec, problems } = await loadSpecWithConfig(
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          spec!,
          redoclyConfig,
        ));
      } else {
        // If local file
        if (debug) {
          console.log('[REDOCUSAURUS_PLUGIN] reading file: ', spec);
        }

        const fileBundle = await bundle({
          ref: spec,
          config: redoclyConfig,
        });

        ({ bundle: bundledSpec, problems } = fileBundle);

        filesToWatch = [path.resolve(spec), ...fileBundle.fileDependencies];
      }

      if (problems?.length) {
        console.error('[REDOCUSAURUS_PLUGIN] errors while bundling spec', spec);

        formatProblems(problems, {
          totals: getTotals(problems),
          version,
        });
      }

      if (debug) {
        console.log('[REDOCUSAURUS_PLUGIN] File Bundled');
      }
      // Pass again to loader to convert swagger to openapi
      const converted = await loadAndBundleSpec(bundledSpec.parsed);

      // If download url is not provided then use bundled yaml as a static file (see `postBuild`)
      url = url || fileName;

      return {
        converted,
        bundle: bundledSpec.parsed,
      };
    },
    async contentLoaded({ content, actions }) {
      const { createData, addRoute, setGlobalData } = actions;
      if (!content?.converted) {
        throw new Error(`[Redocusaurus] Spec could not be parsed: ${spec}`);
      }

      const data: SpecProps = {
        url,
        themeId,
        isSpecFile,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        spec: content.converted as any,
      };
      setGlobalData(data);

      if (options.route) {
        const routePath = options.route.startsWith('/')
          ? options.route.slice(1)
          : options.route;

        const specProps = await createData(
          `redocApiSpecV1.2-${options.id || '1'}.json`,
          JSON.stringify(data),
        );
        const layoutProps = await createData(
          `redocApiLayoutV1-${options.id || '1'}.json`,
          JSON.stringify(options.layout),
        );

        const modules: Record<keyof ApiDocProps, string> = {
          specProps,
          layoutProps,
        };

        const routeOptions = {
          modules,
          component: '@theme/ApiDoc',
          exact: true,
          path: normalizeUrl([baseUrl, routePath]),
        };

        if (debug) {
          console.error('[REDOCUSAURUS_PLUGIN] Route:', routeOptions);
        }
        addRoute(routeOptions);
      }
    },
    async postBuild({ content }) {
      if (!isSpecFile || downloadUrl) {
        return;
      }
      // Create a static file from bundled spec
      const staticFile = path.join(context.outDir, fileName);
      const dir = path.dirname(staticFile);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir);
      }
      if (debug) {
        console.error(
          '[REDOCUSAURUS_PLUGIN] creating static bundle copy for download',
          staticFile,
        );
      }
      // create bundled url
      const bundledYaml = stringifyYaml(content.bundle || content.converted);
      fs.writeFileSync(staticFile, bundledYaml);
    },
    getPathsToWatch() {
      return filesToWatch;
    },
  };
}

export function validateOptions({
  options,
  validate,
}: OptionValidationContext<
  typeof PluginOptionSchema,
  PluginOptions
>): PluginOptions {
  const validatedOptions = validate(PluginOptionSchema, options);
  return validatedOptions;
}
