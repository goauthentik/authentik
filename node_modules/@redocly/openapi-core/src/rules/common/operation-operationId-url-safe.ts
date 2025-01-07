import { Oas3Rule, Oas2Rule } from '../../visitors';
import { Oas2Operation } from '../../typings/swagger';
import { Oas3Operation } from '../../typings/openapi';
import { UserContext } from '../../walk';

const validUrlSymbols = /^[A-Za-z0-9-._~:/?#\[\]@!\$&'()*+,;=]*$/;

export const OperationIdUrlSafe: Oas3Rule | Oas2Rule = () => {
  return {
    Operation(operation: Oas2Operation | Oas3Operation, { report, location }: UserContext) {
      if (operation.operationId && !validUrlSymbols.test(operation.operationId)) {
        report({
          message: 'Operation `operationId` should not have URL invalid characters.',
          location: location.child(['operationId']),
        });
      }
    },
  };
};
