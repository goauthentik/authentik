import { parseYaml } from '../js-yaml';
import { Document, Source } from '../resolve';
import { Oas3RuleSet } from '../oas-types';
import { StyleguideConfig, mergeExtends, resolvePlugins } from '../config';

import type { RuleConfig, Plugin, ResolvedStyleguideConfig } from '../config/types';

export function parseYamlToDocument(body: string, absoluteRef: string = ''): Document {
  return {
    source: new Source(absoluteRef, body),
    parsed: parseYaml(body, { filename: absoluteRef }),
  };
}

export function makeConfigForRuleset(rules: Oas3RuleSet, plugin?: Partial<Plugin>) {
  const rulesConf: Record<string, RuleConfig> = {};
  const ruleId = 'test';
  Object.keys(rules).forEach((name) => {
    rulesConf[`${ruleId}/${name}`] = 'error';
  });
  const extendConfigs = [
    resolvePlugins([
      {
        ...plugin,
        id: ruleId,
        rules: { oas3: rules },
      },
    ]) as ResolvedStyleguideConfig,
  ];
  if (rules) {
    extendConfigs.push({ rules });
  }
  const styleguide = mergeExtends(extendConfigs);

  return new StyleguideConfig(styleguide);
}
