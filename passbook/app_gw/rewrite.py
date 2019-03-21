"""passbook app_gw rewriter"""

from passbook.app_gw.models import RewriteRule


class Context:
    """Empty class which we dynamically add attributes to"""

class Rewriter:
    """Apply rewrites"""

    __application = None
    __request = None

    def __init__(self, application, request):
        self.__application = application
        self.__request = request

    def __build_context(self, matches):
        """Build object with .0, .1, etc as groups and give access to request"""
        context = Context()
        for index, group_match in enumerate(matches.groups()):
            setattr(context, "g%d" % (index + 1), group_match)
        setattr(context, 'request', self.__request)
        return context

    def build(self):
        """Run all rules over path and return final path"""
        path = self.__request.get_full_path()
        for rule in RewriteRule.objects.filter(provider__in=[self.__application]):
            matches = rule.compiled_matcher.search(path)
            if not matches:
                continue
            replace_context = self.__build_context(matches)
            path = rule.replacement.format(context=replace_context)
            if rule.halt:
                return path
        return path
