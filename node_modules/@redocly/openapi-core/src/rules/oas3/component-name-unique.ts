import { Problem, UserContext } from '../../walk';
import { Oas2Rule, Oas3Rule, Oas3Visitor } from '../../visitors';
import {
  Oas3Definition,
  Oas3Parameter,
  Oas3RequestBody,
  Oas3Response,
  Oas3Schema,
  OasRef,
} from '../../typings/openapi';

const TYPE_NAME_SCHEMA = 'Schema';
const TYPE_NAME_PARAMETER = 'Parameter';
const TYPE_NAME_RESPONSE = 'Response';
const TYPE_NAME_REQUEST_BODY = 'RequestBody';

const TYPE_NAME_TO_OPTION_COMPONENT_NAME: { [key: string]: string } = {
  [TYPE_NAME_SCHEMA]: 'schemas',
  [TYPE_NAME_PARAMETER]: 'parameters',
  [TYPE_NAME_RESPONSE]: 'responses',
  [TYPE_NAME_REQUEST_BODY]: 'requestBodies',
};

export const ComponentNameUnique: Oas3Rule | Oas2Rule = (options) => {
  const components = new Map<string, Set<string>>();

  const typeNames: string[] = [];
  if (options.schemas !== 'off') {
    typeNames.push(TYPE_NAME_SCHEMA);
  }
  if (options.parameters !== 'off') {
    typeNames.push(TYPE_NAME_PARAMETER);
  }
  if (options.responses !== 'off') {
    typeNames.push(TYPE_NAME_RESPONSE);
  }
  if (options.requestBodies !== 'off') {
    typeNames.push(TYPE_NAME_REQUEST_BODY);
  }

  const rule: Oas3Visitor = {
    ref: {
      leave(ref: OasRef, { type, resolve }: UserContext) {
        const typeName = type.name;
        if (typeNames.includes(typeName)) {
          const resolvedRef = resolve(ref);
          if (!resolvedRef.location) return;

          addComponentFromAbsoluteLocation(
            typeName,
            resolvedRef.location.absolutePointer.toString()
          );
        }
      },
    },
    Root: {
      leave(root: Oas3Definition, ctx: UserContext) {
        components.forEach((value, key, _) => {
          if (value.size > 1) {
            const component = getComponentFromKey(key);
            const optionComponentName = getOptionComponentNameForTypeName(component.typeName);
            const definitions = Array.from(value)
              .map((v) => `- ${v}`)
              .join('\n');

            const problem: Problem = {
              message: `Component '${optionComponentName}/${component.componentName}' is not unique. It is defined at:\n${definitions}`,
            };

            const componentSeverity = optionComponentName ? options[optionComponentName] : null;
            if (componentSeverity) {
              problem.forceSeverity = componentSeverity;
            }
            ctx.report(problem);
          }
        });
      },
    },
  };

  if (options.schemas != 'off') {
    rule.NamedSchemas = {
      Schema(_: Oas3Schema, { location }: UserContext) {
        addComponentFromAbsoluteLocation(TYPE_NAME_SCHEMA, location.absolutePointer.toString());
      },
    };
  }

  if (options.responses != 'off') {
    rule.NamedResponses = {
      Response(_: Oas3Response, { location }: UserContext) {
        addComponentFromAbsoluteLocation(TYPE_NAME_RESPONSE, location.absolutePointer.toString());
      },
    };
  }

  if (options.parameters != 'off') {
    rule.NamedParameters = {
      Parameter(_: Oas3Parameter, { location }: UserContext) {
        addComponentFromAbsoluteLocation(TYPE_NAME_PARAMETER, location.absolutePointer.toString());
      },
    };
  }

  if (options.requestBodies != 'off') {
    rule.NamedRequestBodies = {
      RequestBody(_: Oas3RequestBody, { location }: UserContext) {
        addComponentFromAbsoluteLocation(
          TYPE_NAME_REQUEST_BODY,
          location.absolutePointer.toString()
        );
      },
    };
  }

  return rule;

  function getComponentNameFromAbsoluteLocation(absoluteLocation: string): string {
    const componentName = absoluteLocation.split('/').slice(-1)[0];
    if (
      componentName.endsWith('.yml') ||
      componentName.endsWith('.yaml') ||
      componentName.endsWith('.json')
    ) {
      return componentName.slice(0, componentName.lastIndexOf('.'));
    }
    return componentName;
  }

  function addFoundComponent(
    typeName: string,
    componentName: string,
    absoluteLocation: string
  ): void {
    const key = getKeyForComponent(typeName, componentName);
    const locations = components.get(key) ?? new Set();
    locations.add(absoluteLocation);
    components.set(key, locations);
  }

  function addComponentFromAbsoluteLocation(typeName: string, absoluteLocation: string): void {
    const componentName = getComponentNameFromAbsoluteLocation(absoluteLocation);
    addFoundComponent(typeName, componentName, absoluteLocation);
  }
};

function getOptionComponentNameForTypeName(typeName: string): string | null {
  return TYPE_NAME_TO_OPTION_COMPONENT_NAME[typeName] ?? null;
}

function getKeyForComponent(typeName: string, componentName: string): string {
  return `${typeName}/${componentName}`;
}

function getComponentFromKey(key: string): { typeName: string; componentName: string } {
  const [typeName, componentName] = key.split('/');
  return { typeName, componentName };
}
