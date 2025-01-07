import type { Oas2Rule } from '../../visitors';
import type { UserContext } from '../../walk';
import { validateMimeType } from '../../utils';

export const ResponseMimeType: Oas2Rule = ({ allowedValues }) => {
  return {
    Root(root, ctx: UserContext) {
      validateMimeType({ type: 'produces', value: root }, ctx, allowedValues);
    },
    Operation: {
      leave(operation, ctx: UserContext) {
        validateMimeType({ type: 'produces', value: operation }, ctx, allowedValues);
      },
    },
  };
};
