```
 virtualenv venv --python=python3.5
 pip install django graphene-django
 source venv/bin/activate
 django-admin startproject cookbook
 cd cookbook/
 django-admin startapp ingedients
 python manage.py migrate
```
editamos el modelo `cookbook/ingedients/models.py`:
```python
from django.db import models

class Category(models.Model):
  name=models.CharField(max_length=100)

  def __str__(self):
    return self.name

class Ingredient(models.Model):
  name=models.CharField(max_length=100)
  notes=models.TextField()
  category=models.ForeignKey(Category,related_name='ingredients', on_delete=models.CASCADE)

  def __str__(self):
    return self.name
```

agregar al `settings.py`:
```python
INSTALLED_APPS = [
    ...
    # Install the ingredients app
    'cookbook.ingredients',
]
```

siempre despues de modificar los modelos remigrar:
```
python manage.py makemigrations
python manage.py migrate
```
creamos un archivo `cookbook/ingredients.json`:
```json
[{"model": "ingredients.category", "pk": 1,
 "fields": {"name": "Dairy"}},
 {"model": "ingredients.category",
 "pk": 2,
 "fields": {"name": "Meat"}},
 {"model": "ingredients.ingredient",
 "pk": 1,
 "fields": {"name": "Eggs",
 "notes": "Good old eggs",
 "category": 1}},
 {"model": "ingredients.ingredient",
 "pk": 2,
 "fields": {"name": "Milk",
 "notes": "Comes from a cow",
 "category": 1}},
 {"model": "ingredients.ingredient",
 "pk": 3,
 "fields": {"name": "Beef",
 "notes": "Much like milk, this comes from a cow",
 "category": 2}},
 {"model": "ingredients.ingredient",
 "pk": 4,
 "fields": {"name": "Chicken",
 "notes": "Definitely doesn't come from a cow",
 "category": 2}}]
```
y llenar la base de datos :
```
python manage.py loaddata ingredients
```

crear superusuario y luego agregar al `ingredients/admin.py`:
```python
from django.contrib import admin
from ingredients.models import Category, Ingredient

admin.site.register(Category)
admin.site.register(Ingredient)
```
necesitamos:
+ schema con los typos object definidos
+ una vista que tome las querys y responda

graphene necesita saber el tipo de los objetos para crear el grafo
este sera el root type a partir del cual todo acceso inicia(es la query class)
 para cada modelo hay que crear su tipo subclaseandolo como `DjangoObjectType`

doc:
la clase Query es un mixin, inheriting de object, estoe s por que creamos una clase query a nivel proyecto que convina todos nuestros mixines a nivel app(creoq ue es por que es una unica query que junta todo)

creamos un schema en `cookbook/schema.py` que maneja las subquerys como el urls:

```python
import graphene
import ingredients.schema

class Query(ingredients.schema.Query, graphene.ObjectType):
  # This class will inherit from multiple Queries
  # as we begin to add more apps to our project
  pass

schema=graphene.Schema(query=Query)
```

hay que agregar `al settings.py`:
```python
INSTALLED_APPS = [
    ...
    'graphene_django',
]
...
GRAPHENE = {
    'SCHEMA': 'cookbook.schema.schema'
}

```
### vistas
GraphQLView administra las vistas, no como en REST
 agregar al `cookbook/urls.py`:
 ```python
from django.conf.urls import url, include
from django.contrib import admin

from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    #podria ser tambien graphql', especificando el schema
    #path(GraphQLView.as_view(graphiql=True, schema=schema)),
    path('graphql/',GraphQLView.as_view(graphiql=True)),
]
```


**esto es diferente del primer proyecto**
Aqui usaremos relay, tengo mis dudas de si usarlo ya que no lo pinso usar pero internamente nos administra facilmente las rutas...entonces si lo puedo usar en frontend directamente con react si no hay problemas del estandar relay lo uso
si no mal entiendo ya provee muchas funcionalidades como mutations y busqueda incluida

crear un archivo `cookbook/ingredients/schema.py`:
```python
from graphene import relay, ObjectType
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from ingredients.models import Category, Ingredient

class CategoryNode(DjangoObjectType):
  class Meta:
    model=Category
    filter_fields=['name','ingredients']
    interfaces=(relay.Node,)


class IngredientNode(DjangoObjectType):
  class Meta:
    model=Ingredient
    filter_fields={
    'name':['exact','icontains','istartswith'],
    'notes':['exact','icontains'],
    'category':['exact'],
    'category__name':['exact'],
    }
    interfaces=(relay.Node,)

class Query(object):
  category=relay.Node.Field(CategoryNode)
  all_categories=DjangoFilterConnectionField(CategoryNode)
  ingredient=relay.Node.Field(IngredientNode)
  all_ingredients=DjangoFilterConnectionField(IngredientNode)
```

hay que instalar :
```
pip install django-filter
```

y eso ya nos permite hacer multiples peticiones individuales:
```js
query {
  cat1:category(id: 1) {
    name
  }
  anotherCategory: category(name: "Dairy") {
    ingredients {
      id
      name
    }
  }
}
```
al hacerlo con relay solo se maneja a nivel de grafo :/
pero nos deja hacer busquedas sin tener que implementarlas :O
```
query {
  allIngredients {
    edges {
      node {
        id,
        name
      }
    }
  }
}

query {
  # Graphene creates globally unique IDs for all objects.
  # You may need to copy this value from the results of the first query
  ingredient(id: "SW5ncmVkaWVudE5vZGU6MQ==") {
    name
  }
}


query {
  # You can also use `category: "CATEGORY GLOBAL ID"`
  allIngredients(name_Icontains: "e", category_Name: "Meat") {
    edges {
      node {
        name
      }
    }
  }
}
```
se pueden usar los filtros sin tener que usar relay
editamos su schema.py:
```python
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
        'notes': ['exact', 'icontains'],
        'category': ['exact'],
        'category__name': ['exact'],
    }


class Query(object):
  category = Node.Field(CategoryNode)
  all_categories = DjangoFilterConnectionField(CategoryNode)

  ingredient = Node.Field(IngredientNode)
  all_ingredients = DjangoFilterConnectionField(IngredientNode)
```
y podemos hacer varias querys:
```

{
  allCategories(name: "Dairy") {
    edges {
      node {
        id
        name
        ingredients {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
  }
}

{
  allIngredients(notes_Icontains:"comes"){
    edges{node{
      id
      name
      notes
    }}
  }
}

```
las busquedas se pueden hacer con los aprametros indicados en el filtro ej:name_Icontains
no se si se puedan usar filtros sin nodos, creoq ue no pero al parecer es ams facil por la creacion automatica de busquedas, falta revisar las mutations por que no vienen en la documentacion
