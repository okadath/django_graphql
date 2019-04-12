
aqui creamos las mutaciones solo con el modelo Node
no se si ya vengan las CRUDS or default con relay
el graphql usa el ORM de django para la modifiacion de los datos

no previene por default los valores duplicados(como django)
eso se debe de prevenir antes
agregamos al models.pyel valor unique y al aprecer se debe hacer un filtrado para esto(aun no lo hago):
```python
class Category(models.Model):
  name=models.CharField(max_length=100,unique=True)
```
tambien se debe de traerlos datos de vuelta manualmente

solo modificamos el schema(da igual solo usar Node o Relay.Node):
```python
from ingredients.models import Category, Ingredient
import graphene
from graphene import Node,relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from graphene import ObjectType, InputObjectType
# Graphene will automatically map the Category model's fields onto the CategoryNode.
# This is configured in the CategoryNode's Meta class (as you can see below)
class CategoryNode(DjangoObjectType):
  class Meta:
    model = Category
    interfaces = (relay.Node, )
    filter_fields = ['name', 'ingredients']

class IngredientNode(DjangoObjectType):
  class Meta:
    model = Ingredient
    # Allow for some more advanced filtering here
    interfaces = (relay.Node, )
    filter_fields = {
        'name': ['exact', 'icontains', 'istartswith'],
        'notes': ['exact', 'icontains', 'istartswith'],
        'category': ['exact'],
        'category__name': ['exact'],
    }

class CreateCategory(graphene.Mutation):
  #campos de salida
  id = graphene.ID()
  name = graphene.String()
  #campos enviados al server
  class Arguments:
    name = graphene.String()
    #enlaza DB con los datos
  def mutate(self, info, **args):
    cat=Category(name=args['name'])
    cat.save()
    cat2=Category.objects.get(name=cat.name)
    print(cat2.id)
    return CreateCategory(id=cat.id,name=cat.name)

class DeleteCategory(graphene.Mutation):
  id = graphene.ID()
  name = graphene.String()
  class Arguments:
    name = graphene.String()
  def mutate(self, info, **args):
    cat2=Category.objects.get(name=args['name'])
    cat2.delete()
    return DeleteCategory(id="asd",name=cat2.name)


class Query(object):
  category = relay.Node.Field(CategoryNode)
  all_categories = DjangoFilterConnectionField(CategoryNode)

  ingredient = relay.Node.Field(IngredientNode)
  all_ingredients = DjangoFilterConnectionField(IngredientNode)

  def resolve_categories(self):
    return Category.objects.all()

class Mutation(graphene.ObjectType):
  # create_ingredient = CreateIngredient.Field()
  create_category=CreateCategory.Field()
  delete_category=DeleteCategory.Field()

  def resolve_category(self,id):
    return Category.objects.get(id=id)


```


en este iniciamos con el proyecto 2 y lo modificamos par poder tener mutations:

```
{
  allIngredients(name_Istartswith:"b"){
    edges{
      node{
        id
        name
      }
    }
  }
}
```
con variables:

```
query byyid($var:String!){
  asd:allIngredients(name_Istartswith:$var){
    edges{
      node{
        id
        name
      }
    }
  }
  
}
{"var":"Eg"}
```
mutaciones
```
mutation my{
  createCategory(name:"as"){
    name
  }
}

mutation my{
deleteCategory(name:"test2"){
  id
  name
  
}
}
```