import type { Config, Source, Document } from '@redocly/openapi-core';
import { bundle } from '@redocly/openapi-core';

/**
 * Based on loadAndBundleSpec from redoc.
 * Customized to pass custom loaded config
 * @see https://github.com/Redocly/redoc/blob/33be51a7a4068f44fd914314002c058a204ba0c2/src/utils/loadAndBundleSpec.ts
 */
export async function loadSpecWithConfig(
  specUrlOrObject: object | string,
  config: Config,
) {
  const bundleOpts: Parameters<typeof bundle>[0] = {
    config,
    base: process.cwd(),
  };

  if (typeof specUrlOrObject === 'object' && specUrlOrObject !== null) {
    bundleOpts.doc = {
      source: { absoluteRef: '' } as Source,
      parsed: specUrlOrObject,
    } as Document;
  } else {
    bundleOpts.ref = specUrlOrObject;
  }

  return bundle(bundleOpts);
}
