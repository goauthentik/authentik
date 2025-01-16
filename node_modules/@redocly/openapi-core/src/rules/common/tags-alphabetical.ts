import { Oas3Rule, Oas2Rule } from '../../visitors';
import { Oas2Definition, Oas2Tag } from '../../typings/swagger';
import { Oas3Definition, Oas3Tag } from '../../typings/openapi';
import { UserContext } from '../../walk';

export const TagsAlphabetical: Oas3Rule | Oas2Rule = ({ ignoreCase = false }) => {
  return {
    Root(root: Oas2Definition | Oas3Definition, { report, location }: UserContext) {
      if (!root.tags) return;
      for (let i = 0; i < root.tags.length - 1; i++) {
        if (getTagName(root.tags[i], ignoreCase) > getTagName(root.tags[i + 1], ignoreCase)) {
          report({
            message: 'The `tags` array should be in alphabetical order.',
            location: location.child(['tags', i]),
          });
        }
      }
    },
  };
};

function getTagName(tag: Oas2Tag | Oas3Tag, ignoreCase: boolean): string {
  return ignoreCase ? tag.name.toLowerCase() : tag.name;
}
