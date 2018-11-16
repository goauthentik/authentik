# from rest_framework.serializers import HyperlinkedModelSerializer
# from passbook.admin.api.v1.utils import LookupSerializer
# from passbook.core.models import Source
# from passbook.oauth_client.models import OAuthSource

# from rest_framework.viewsets import ModelViewSet

# class LookupSourceSerializer(HyperlinkedModelSerializer):

#     def to_representation(self, instance):
#         if isinstance(instance, Source):
#             return SourceSerializer(instance=instance).data
#         elif isinstance(instance, OAuthSource):
#             return OAuthSourceSerializer(instance=instance).data
#         else:
#             return LookupSourceSerializer(instance=instance).data

#     class Meta:
#         model = Source
#         fields = '__all__'


# class SourceViewSet(ModelViewSet):

#     serializer_class = LookupSourceSerializer
#     queryset = Source.objects.select_subclasses()
