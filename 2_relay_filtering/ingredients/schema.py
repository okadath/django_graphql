from ingredients.models import Category, Ingredient
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


# Graphene will automatically map the Category model's fields onto the CategoryNode.
# This is configured in the CategoryNode's Meta class (as you can see below)
class CategoryNode(DjangoObjectType):

	class Meta:
		model = Category
		interfaces = (Node, )
		filter_fields = ['name', 'ingredients']


class IngredientNode(DjangoObjectType):

	class Meta:
		model = Ingredient
		# Allow for some more advanced filtering here
		interfaces = (Node, )
		filter_fields = {
		    'name': ['exact', 'icontains', 'istartswith'],
		    'notes': ['exact', 'icontains', 'istartswith'],
		    'category': ['exact'],
		    'category__name': ['exact'],
		}


class Query(object):
	category = Node.Field(CategoryNode)
	all_categories = DjangoFilterConnectionField(CategoryNode)

	ingredient = Node.Field(IngredientNode)
	all_ingredients = DjangoFilterConnectionField(IngredientNode)
# from graphene import relay, ObjectType
# from graphene_django.types import DjangoObjectType
# from graphene_django.filter import DjangoFilterConnectionField

# from ingredients.models import Category, Ingredient

# class CategoryNode(DjangoObjectType):
# 	class Meta:
# 		model=Category
# 		filter_fields=['name','ingredients']
# 		interfaces=(relay.Node,)


# class IngredientNode(DjangoObjectType):
# 	class Meta:
# 		model=Ingredient
# 		filter_fields={
# 		'name':['exact','icontains','istartswith'],
# 		'notes':['exact','icontains'],
# 		'category':['exact'],
# 		'category__name':['exact'],
# 		}
# 		interfaces=(relay.Node,)

# class Query(object):
# 	category=relay.Node.Field(CategoryNode)
# 	all_categories=DjangoFilterConnectionField(CategoryNode)
# 	ingredient=relay.Node.Field(IngredientNode)
# 	all_ingredients=DjangoFilterConnectionField(IngredientNode)