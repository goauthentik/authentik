import { Config, loadConfig } from '@redocly/openapi-core';

export async function loadRedoclyConfig(
  config?: string | unknown,
): Promise<Config> {
  let redoclyConfig: Config;

  if (config) {
    if (typeof config === 'string') {
      redoclyConfig = await loadConfig({
        configPath: config,
      });
    } else {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      redoclyConfig = new Config(config as any);
    }
  } else {
    redoclyConfig = await loadConfig();
  }

  return redoclyConfig;
}
