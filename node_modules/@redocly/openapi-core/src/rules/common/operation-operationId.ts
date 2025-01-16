import { Oas3Rule, Oas2Rule } from '../../visitors';
import { validateDefinedAndNonEmpty } from '../utils';
import { UserContext } from '../../walk';
import { Oas2Operation } from '../../typings/swagger';
import { Oas3Operation } from '../../typings/openapi';

export const OperationOperationId: Oas3Rule | Oas2Rule = () => {
  return {
    Root: {
      PathItem: {
        Operation(operation: Oas2Operation | Oas3Operation, ctx: UserContext) {
          validateDefinedAndNonEmpty('operationId', operation, ctx);
        },
      },
    },
  };
};
