import { Oas3Rule } from '../../visitors';
import { Location, isRef } from '../../ref-utils';
import { Oas3Example } from '../../typings/openapi';
import { getAdditionalPropertiesOption, validateExample } from '../utils';
import { UserContext } from '../../walk';

export const ValidContentExamples: Oas3Rule = (opts) => {
  const allowAdditionalProperties = getAdditionalPropertiesOption(opts) ?? false;

  return {
    MediaType: {
      leave(mediaType, ctx: UserContext) {
        const { location, resolve } = ctx;
        if (!mediaType.schema) return;
        if (mediaType.example !== undefined) {
          resolveAndValidateExample(mediaType.example, location.child('example'));
        } else if (mediaType.examples) {
          for (const exampleName of Object.keys(mediaType.examples)) {
            resolveAndValidateExample(
              mediaType.examples[exampleName],
              location.child(['examples', exampleName, 'value']),
              true
            );
          }
        }

        function resolveAndValidateExample(
          example: Oas3Example | any,
          location: Location,
          isMultiple?: boolean
        ) {
          if (isRef(example)) {
            const resolved = resolve<Oas3Example>(example);
            if (!resolved.location) return;
            location = isMultiple ? resolved.location.child('value') : resolved.location;
            example = resolved.node;
          }
          if (isMultiple && typeof example.value === 'undefined') {
            return;
          }
          validateExample(
            isMultiple ? example.value : example,
            mediaType.schema!,
            location,
            ctx,
            allowAdditionalProperties
          );
        }
      },
    },
  };
};
