import { Oas3Rule, Oas2Rule } from '../../visitors';
import { validateDefinedAndNonEmpty } from '../utils';
import { UserContext } from '../../walk';
import { Oas2Operation } from '../../typings/swagger';
import { Oas3Operation } from '../../typings/openapi';

export const OperationSummary: Oas3Rule | Oas2Rule = () => {
  return {
    Operation(operation: Oas2Operation | Oas3Operation, ctx: UserContext) {
      validateDefinedAndNonEmpty('summary', operation, ctx);
    },
  };
};
