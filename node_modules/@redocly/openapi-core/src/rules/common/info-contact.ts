import { Oas3Rule, Oas2Rule } from '../../visitors';
import { missingRequiredField } from '../utils';

export const InfoContact: Oas3Rule | Oas2Rule = () => {
  return {
    Info(info, { report, location }) {
      if (!info.contact) {
        report({
          message: missingRequiredField('Info', 'contact'),
          location: location.child('contact').key(),
        });
      }
    },
  };
};
