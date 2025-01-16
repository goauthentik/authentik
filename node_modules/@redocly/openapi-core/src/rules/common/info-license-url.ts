import { Oas3Rule, Oas2Rule } from '../../visitors';
import { validateDefinedAndNonEmpty } from '../utils';

export const InfoLicenseUrl: Oas3Rule | Oas2Rule = () => {
  return {
    License(license, ctx) {
      validateDefinedAndNonEmpty('url', license, ctx);
    },
  };
};
