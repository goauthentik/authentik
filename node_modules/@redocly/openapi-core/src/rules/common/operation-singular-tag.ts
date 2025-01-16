import { Oas3Rule, Oas2Rule } from '../../visitors';
import { Oas2Operation } from '../../typings/swagger';
import { Oas3Operation } from '../../typings/openapi';
import { UserContext } from '../../walk';

export const OperationSingularTag: Oas3Rule | Oas2Rule = () => {
  return {
    Operation(operation: Oas2Operation | Oas3Operation, { report, location }: UserContext) {
      if (operation.tags && operation.tags.length > 1) {
        report({
          message: 'Operation `tags` object should have only one tag.',
          location: location.child(['tags']).key(),
        });
      }
    },
  };
};
