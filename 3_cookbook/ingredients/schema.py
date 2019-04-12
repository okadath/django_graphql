from ingredients.models import Category, Ingredient
import graphene
from graphene import Node
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from graphene import ObjectType, InputObjectType
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

class CreateCategory(graphene.Mutation):
	#campos de salida
  id = graphene.Int()
  name = graphene.String()
  #campos enviados al server
  class Arguments:
    name = graphene.String()
    #enlaza DB con los datos
  def mutate(self, info, name):
	  cat = Category(name=name)
	  cat.save()
	  return CreateCategory(name=cat.name)



class Query(object):
	category = Node.Field(CategoryNode)
	all_categories = DjangoFilterConnectionField(CategoryNode)

	ingredient = Node.Field(IngredientNode)
	all_ingredients = DjangoFilterConnectionField(IngredientNode)

	def resolve_categories(self):
		return Category.objects.all()
#esta linea va si no hay mas querys
#si si hay mas va en el schema de la app principal
# schema = graphene.Schema(query=Query,)    

# #4 no se cual es la buena si esta o solo object
#ambos jalan igual de bien
# class Mutation(graphene.ObjectType):
#   create_cat = CreateCategory.Field()

class Mutation(graphene.ObjectType):
     # create_ingredient = CreateIngredient.Field()
     create_category=CreateCategory.Field()
    
