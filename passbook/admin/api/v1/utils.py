"""passbook admin api utils"""
# from django.db.models import Model
# from rest_framework.serializers import ModelSerializer


# class LookupSerializer(ModelSerializer):

#     mapping = {}

#     def to_representation(self, instance):
#         for __model, __serializer in self.mapping.items():
#             if isinstance(instance, __model):
#                 return __serializer(instance=instance).to_representation(instance)
#         raise KeyError(instance.__class__.__name__)

#     class Meta:
#         model = Model
#         fields = '__all__'
