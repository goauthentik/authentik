import { Oas3Rule, Oas2Rule } from '../../visitors';
import { Oas2Definition, Oas2Operation } from '../../typings/swagger';
import { Oas3Definition, Oas3Operation } from '../../typings/openapi';
import { UserContext } from '../../walk';

export const OperationTagDefined: Oas3Rule | Oas2Rule = () => {
  let definedTags: Set<string>;

  return {
    Root(root: Oas2Definition | Oas3Definition) {
      definedTags = new Set((root.tags ?? []).map((t) => t.name));
    },
    Operation(operation: Oas2Operation | Oas3Operation, { report, location }: UserContext) {
      if (operation.tags) {
        for (let i = 0; i < operation.tags.length; i++) {
          if (!definedTags.has(operation.tags[i])) {
            report({
              message: `Operation tags should be defined in global tags.`,
              location: location.child(['tags', i]),
            });
          }
        }
      }
    },
  };
};
