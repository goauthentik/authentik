import type { Oas2Rule } from '../../visitors';
import type { UserContext } from '../../walk';
import { validateMimeType } from '../../utils';

export const RequestMimeType: Oas2Rule = ({ allowedValues }) => {
  return {
    Root(root, ctx: UserContext) {
      validateMimeType({ type: 'consumes', value: root }, ctx, allowedValues);
    },
    Operation: {
      leave(operation, ctx: UserContext) {
        validateMimeType({ type: 'consumes', value: operation }, ctx, allowedValues);
      },
    },
  };
};
