import { Oas3Rule, Oas2Rule } from '../../visitors';
import { missingRequiredField } from '../utils';

export const InfoLicense: Oas3Rule | Oas2Rule = () => {
  return {
    Info(info, { report }) {
      if (!info.license) {
        report({
          message: missingRequiredField('Info', 'license'),
          location: { reportOnKey: true },
        });
      }
    },
  };
};
