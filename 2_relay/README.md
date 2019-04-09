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
**esto es diferente del primer proyecto**

crear un archivo `cookbook/ingredients/schema.py`:
```python
import graphene
from graphene_django.types import DjangoObjectType
from ingredients.models import Category, Ingredient

class CategoryType(DjangoObjectType):
	class Meta:
		model=Category


class IngredientType(DjangoObjectType):
	class Meta:
		model=Ingredient

class Query(object):
	all_categories=graphene.List(CategoryType)
	all_ingredients=graphene.List(IngredientType)

	def resolve_all_categories(self,info,**kwargs):
		return Category.objects.all()
	# We can easily optimize query count in the resolve method
	def resolve_all_ingredients(self, info, **kwargs):
		return Ingredient.objects.select_related('category').all()
```


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

si abrimos `http://localhost:8000/graphql/` nos sale el entorno de graphiql desde donde podemos ver el comportamiento de las querys:
 ```js
query {
  allCategories{
    name
    id
    ingredients {
      name
    }
  }
}
```
