import { Oas3Rule, Oas2Rule } from '../../visitors';
import { Oas2Operation } from '../../typings/swagger';
import { Oas3Operation } from '../../typings/openapi';
import { UserContext } from '../../walk';

export const OperationIdUnique: Oas3Rule | Oas2Rule = () => {
  const seenOperations = new Set();

  return {
    Operation(operation: Oas2Operation | Oas3Operation, { report, location }: UserContext) {
      if (!operation.operationId) return;
      if (seenOperations.has(operation.operationId)) {
        report({
          message: 'Every operation must have a unique `operationId`.',
          location: location.child([operation.operationId]),
        });
      }
      seenOperations.add(operation.operationId);
    },
  };
};
