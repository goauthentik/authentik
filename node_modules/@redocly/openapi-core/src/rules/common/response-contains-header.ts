import { Oas2Rule, Oas3Rule } from '../../visitors';
import { UserContext } from '../../walk';
import { Oas3Response } from '../../typings/openapi';
import { Oas2Response } from '../../typings/swagger';
import { getMatchingStatusCodeRange } from '../../utils';

export const ResponseContainsHeader: Oas3Rule | Oas2Rule = (options) => {
  const names: Record<string, string[]> = options.names || {};
  return {
    Operation: {
      Response: {
        enter: (response: Oas2Response | Oas3Response, { report, location, key }: UserContext) => {
          const expectedHeaders =
            names[key] ||
            names[getMatchingStatusCodeRange(key)] ||
            names[getMatchingStatusCodeRange(key).toLowerCase()] ||
            [];
          for (const expectedHeader of expectedHeaders) {
            if (
              !response?.headers ||
              !Object.keys(response?.headers).some(
                (header) => header.toLowerCase() === expectedHeader.toLowerCase()
              )
            ) {
              report({
                message: `Response object must contain a "${expectedHeader}" header.`,
                location: location.child('headers').key(),
              });
            }
          }
        },
      },
    },
  };
};
