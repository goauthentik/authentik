import { Oas3Rule, Oas2Rule } from '../../visitors';
import { validateDefinedAndNonEmpty } from '../utils';

export const TagDescription: Oas3Rule | Oas2Rule = () => {
  return {
    Tag(tag, ctx) {
      validateDefinedAndNonEmpty('description', tag, ctx);
    },
  };
};
