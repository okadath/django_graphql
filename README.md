dependencias:
```
pipenv install django graphene-django  django-filter django-graphql-jwt
```

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
    #podria ser tambien graphql', especificando el schema, habria que importarlo from cookbook.schema import schema
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
por el momento el modelo solo nos permite manejar una lista de usuarios
si queremos acceder a uno solo habra que editarlo

editamos `el schema.py`:
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
	category=graphene.Field(CategoryType,id=graphene.Int(),name=graphene.String())
	ingredient=graphene.Field(IngredientType,id=graphene.Int(),name=graphene.String())

	def resolve_all_categories(self,info,**kwargs):
		return Category.objects.all()
	# We can easily optimize query count in the resolve method
	def resolve_all_ingredients(self, info, **kwargs):
		return Ingredient.objects.select_related('category').all()

	def resolve_category(self,info,**kwargs):
		id=kwargs.get('id')
		name=kwargs.get('name')
		if id is not None:
			return Category.objects.get(pk=id)
		if name is not None:
			return Category.objects.get(name=name)
		return None

	def resolve_ingredient(self,info,**kwargs):
		id=kwargs.get('id')
		name=kwargs.get('name')
		if id is not None:
			return Ingredient.objects.get(pk=id)
		if name is not None:
			return Ingredient.objects.get(name=name)
		return None
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

# parte 2
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



# parte 3

## Mutations
Aqui creamos las mutaciones solo con el modelo Node
no se si ya vengan las CRUDS por default con relay
el graphql usa el ORM de django para la modifiacion de los datos

No previene por default los valores duplicados(como Django)
eso se debe de prevenir antes

Agregamos al `models.py` el valor unique y al parecer se debe hacer un filtrado para esto(aun no lo hago):
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


En este iniciamos con el proyecto 2 y lo modificamos para poder tener mutations:

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


# parte hackernews
### Tuto 
Instalar librerias
```
 pip install django-filter
 pip install django-graphql-jwt
```
Configurar
```
python manage.py startapp links
 python manage.py makemigrations
 python manage.py migrate
 ``` 

En  `python manage.py shell`:
```python
>>> from links.models import Link
>>> Link.objects.create(url='https://www.howtographql.com/', description='The Fullstack Tutorial for GraphQL')
<Link: Link object (1)>
>>> Link.objects.create(url='https://twitter.com/jonatasbaldin/', description='The Jonatas Baldin Twitter')
<Link: Link object (2)>
>>> 
```
En `link/schema.py` creamos los tipos y la query:
```python
import graphene
from graphene_django import DjangoObjectType
from .models import Link

class LinkType(DjangoObjectType):
    class Meta:
        model = Link

class Query(graphene.ObjectType):
    links = graphene.List(LinkType)

    def resolve_links(self, info, **kwargs):
        return Link.objects.all()
```
En `hackernews/hackernews/schema.py`creamos al query principal:

```python
import graphene
import links.schema

class Query(links.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)

```

y crear en `hackernews/hackernews/urls.py` las urls:
```python
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
]
```
y con esto ya hay querys:
```
query {
  links {
    id
    description
    url
  }
}
```


luego creamos en el `link/schema.py` las mutaciones:
```python
class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()

    #2
    class Arguments:
        url = graphene.String()
        description = graphene.String()

    #3
    def mutate(self, info, url, description):
        link = Link(url=url, description=description)
        link.save()

        return CreateLink(
            id=link.id,
            url=link.url,
            description=link.description,
        )


#4
class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
```
y en el `hackernews/hackernews/schema.py`:
```python
import graphene
import links.schema

class Query(links.schema.Query, graphene.ObjectType):
    pass

class Mutation(links.schema.Mutation, graphene.ObjectType):
    pass
    
schema = graphene.Schema(query=Query, mutation=Mutation)
```
y esto nos permite crear mutations:
```js
mutation{
  createLink(
    url:"http:/asdasdasd"
    description:"shitty shit"
  ){
    id
    url
    description
  }
}
```


## Auth
Creamos una carpeta `users` y ahi un `schema.py` usando el modelo de usuarios de django:
```python
from django.contrib.auth import get_user_model
import graphene
from graphene_django import DjangoObjectType

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
    def mutate(self, info, username, password, email):
        user = get_user_model()(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()
        return CreateUser(user=user)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
```


en la carpeta `hackernews/hackernews/schema.py`lo agregamos a la query principal:
```python
import graphene
import links.schema
import users.schema
class Query(links.schema.Query, graphene.ObjectType):
    pass
class Mutation(users.schema.Mutation, links.schema.Mutation, graphene.ObjectType,):
    pass
schema = graphene.Schema(query=Query, mutation=Mutation)

```

y ya podemos crear usuarios!:
```js
mutation {
  createUser(username: "nuevo",
    email: "asd@asd.com", 
    password: "Qwerty35$") {
    user {
      id
      password
      lastLogin
      isSuperuser
      username
      firstName
      lastName
      email
      isStaff
    }
  }
}
````

para hacer querys de los usuarios agregar al `users/schema.py`:
```python
class Query(graphene.ObjectType):
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()
```
y agregar al schema principal:
```python
class Query(users.schema.Query, links.schema.Query, graphene.ObjectType):
    pass
```

y ya podemos hacer querys listando usuarios:

```
{
users{
  id
  password
  username
  email
}
}
```

## JWT

usaremos insomnia por que gaphiql no permite manejar encabezados http para jwt

agregamos al settings:
```python

GRAPHENE = {
    'SCHEMA': 'hackernews.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

```

modificar el hackernews/hackernews/schema.py:
```python
import graphene
import graphql_jwt
import links.schema
import users.schema

class Query(users.schema.Query, links.schema.Query, graphene.ObjectType):
    pass
class Mutation(users.schema.Mutation, links.schema.Mutation, graphene.ObjectType,):
  token_auth = graphql_jwt.ObtainJSONWebToken.Field()
  verify_token = graphql_jwt.Verify.Field()
  refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
```

con esto ya los puede manejar:

```
mutation{
  tokenAuth(username:"nuevo" password:"Qwerty35$"){
    token
  }
}
```
```
mutation{
verifyToken(token:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmlnSWF0IjoxNTU1MTIxOTM3LCJ1c2VybmFtZSI6Im51ZXZvIiwiZXhwIjoxNTU1MTIyMjM3fQ.bbOlodIcpuSFJ8v8JTE7kL0sQVaQSQhcCwKEDIj1mM4"){
  payload
}
}
```
el tuto nos dice que se debe de refrescar:
```
RefreshToken to obtain a new token within the renewed expiration time for non-expired tokens,
 if they are enabled to expire. Using it is outside the scope of this tutorial.
```
para probar si funciona usaremos una query que me devuelva mi informacion:

en `users/schema.py` modificamos la query:
```python
class Query(graphene.AbstractType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user
```
y para verificar abrimos el cliente de insomnia y ejecutamos las siguientes querys:
```
mutation{
  tokenAuth(
    username:"nuevo",
    password:"Qwerty35$"
  ){
    token
  }
}
```

y eso nos devuelve:
```
{
  "data": {
    "tokenAuth": {
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6Im51ZXZvIiwiZXhwIjoxNTU1MTIyOTA4LCJvcmlnSWF0IjoxNTU1MTIyNjA4fQ.a3TVmW-C0xZ2Nv8HPWqvPn1Wg7G31CHctXYRsKNPewU"
    }
  }
}
```
luego en insomnia en Header agregamos los valores

"Authorization" y "JWT #token"
y hacemos la query que solo se resuelve si estamos logeados:
```
query{
  me{
    id
    username
  }
}
```
 esta nos devuelve nuestros datos
```
{
  "data": {
    "me": {
      "id": "1",
      "username": "nuevo"
    }
  }
}
```
si eliminamos ese header nos manda error:
```
{
  "errors": [
    {
      "path": [
        "me"
      ],
      "message": "Not logged in!",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ]
    }
  ],
  "data": {
    "me": null
  }
}
```


## links con usuarios
editar el 'link/models.py':
```python
from django.db import models
from django.conf import settings

# Create your models here.

class Link(models.Model):
  url=models.URLField()
  description=models.TextField(blank=True)
  posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)
```
y migrar

editar el create link en el links/schema.py:
```python
...
from users.schema import UserType
...
class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)
    ...
    def mutate(self, info, url, description):
        user = info.context.user or None
        link = Link(...,posted_by=user,)
        link.save()

        return CreateLink(
            ...
            posted_by=link.posted_by,
        )

```

y estando logeado ya nos permite ser los creadores de un link:
```
mutation{
  createLink(
    url:"urltestauth"
    description:"demo link con user"
  ){
    id
    url
    description
    postedBy{
      id
      username
      email
    }
  }
}
```

la cual nos devuelve:
```
{
  "data": {
    "createLink": {
      "id": 4,
      "url": "urltestauth",
      "description": "demo link con user",
      "postedBy": {
        "id": "1",
        "username": "nuevo",
        "email": "asd@asd.com"
      }
    }
  }
}
```
## Votos

agregamos al `links.models.py`:

```python
class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    link = models.ForeignKey('links.Link', related_name='votes', on_delete=models.CASCADE)
```
y migrar

luego agregamos a `/links/schema.py`:

```python
from .models import Vote
...
class CreateVote(graphene.Mutation):
    user=graphene.Field(UserType)
    link=graphene.Field(LinkType)
    class Arguments:
        link_id=graphene.Int()
    def mutate(self,info,link_id):
        user=info.context.user
        if user.is_anonymous:
            raise Exception("debes estar logeado para votar")

        link=Link.objects.filter(id=link_id).first()
        if not link:
            raise Exception("link invalido")
    Vote.objects.create(
        user=user,
        link=link,
        )
    return CreateVote(user=user,link=link)
#4
class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
    create_vote=CreateVote.Field()
```

y eso nos permite votar:
```

mutation{
createVote(linkId:1){
  user{
    id
    username
    email
  }
  link{
    id
    description
    postedBy{
      username
    }
    url
  }
  
}
}

{
  "data": {
    "createVote": {
      "user": {
        "id": "1",
        "username": "nuevo",
        "email": "asd@asd.com"
      },
      "link": {
        "id": "1",
        "description": "The Fullstack Tutorial for GraphQL",
        "postedBy": null,
        "url": "https://www.howtographql.com/"
      }
    }
  }
}
```
crear una query para listar los votos

en links/schema.py:
```python
...
class VoteType(DjangoObjectType):
    class Meta:
        model=Vote

class Query(graphene.ObjectType):
    links = graphene.List(LinkType)
    votes=graphene.List(VoteType)
    def resolve_votes(self,info,**kwargs):
        return Vote.objects.all()

    def resolve_links(self, info, **kwargs):
        return Link.objects.all()
...
```

y con eso ya tenemos querys dandonos los votos hechos
por un usuario dado:
```
query{
  votes{
    id
    user{
      id
      username
    }
    link{
      id
      url
      description
      postedBy{
        id
        username
        
      }
    }
  }
}


{
  "data": {
    "votes": [
      {
        "id": "1",
        "user": {
          "id": "1",
          "username": "nuevo"
        },
        "link": {
          "id": "1",
          "url": "https://www.howtographql.com/",
          "description": "The Fullstack Tutorial for GraphQL",
          "postedBy": null
        }
      }
    ]
  }
}
```
una query par amostrar todos los links y sus votos:
```
query{
links{
  id
  id
  votes{
    id
    user{
      id
      username
    }
  }
}
}
```
## Errores

poemos manejar las excepciones normalmente o con su propio metodo de la libreria:
```python
from graphql import GraphQLError
    ...
class CreateVote(graphene.Mutation):
    ...
    def mutate(self,info,link_id):
        user=info.context.user
        if user.is_anonymous:
            raise GraphQLError("debes estar logeado para votar")
```

## Filtrado

usamos los filtros de Django(no los conocia :O)
Aqui es muy importante **El paso de parametros!!**
```python
from django.db.models import Q
...
class Query(graphene.ObjectType):
    links = graphene.List(LinkType,search=graphene.String())
    votes=graphene.List(VoteType)

    def resolve_links(self, info,search=None, **kwargs):
        if search:
            filter=(
                Q(url__icontains=search)|
                Q(description__icontains=search)
                )
            return Link.objects.filter(filter)
        return Link.objects.all()
```
y nos devuelve la busqueda pasada como parametro:
```
query{
links(
  search:"asd"
){
  id
  url
  description
}
}
```
## Paginacion

editamos el `links/schema.py`:
```python
class Query(graphene.ObjectType):
    links = graphene.List(
        LinkType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
        )
    votes=graphene.List(VoteType)

    def resolve_links(self, info, search=None,first=None, skip=None,**kwargs):
        qs=Link.objects.all()
        if search:
            filter=(
                Q(url__icontains=search)|
                Q(description__icontains=search)
                )
            qs=qs.filter(filter)
        if skip:
            qs=qs[skip:]
        if first:
            qs=qs[:first]
        return qs

    def resolve_votes(self,info,**kwargs):
        return Vote.objects.all()
```
y se puede hacer paginacion
first es cuantos devuelve y skip es desde donde inicia
skip=cota de inicio(/////////first=cota de grosor/////////)
```
query{
links(first:2, skip:2){
  id
  url
  description
}
}
```

## Relay

esto lo crearemos en un archivo separado que aun asi agega las querys al modelo :D
en `links` creamos un `schema_relay.py`:
```python
import graphene
import django_filters
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Link, Vote

class LinkFilter(django_filters.FilterSet):
  class Meta:
    model=Link
    fields=['url','description']

class LinkNode(DjangoObjectType):
  class Meta:
    model=Link
    interfaces=(graphene.relay.Node,)

class VoteNode(DjangoObjectType):
  class Meta:
    model=Vote
    interfaces=(graphene.relay.Node,)

class RelayQuery(graphene.ObjectType):
  relay_link=graphene.relay.Node.Field(LinkNode)
  relay_links=DjangoFilterConnectionField(LinkNode,filterset_class=LinkFilter)
```

y al schema principal en `hackernews/hackernews.py`:
```python
import links.schema_relay

class Query(
  users.schema.Query,
  links.schema.Query,
  graphene.ObjectType,
  links.schema_relay.RelayQuery,
  ):
    pass
```
eso ya nos permite hacer querys:
```
query{
  relayLinks
  {edges
  {
    node
    {
      id
      url
      description
      postedBy{
        id
        username
      }
      votes{
        edges{
          node{
            id
            user{id
            username
            }
            link{
              id
              url
              description
            }
            
          }
        }
      }
    }
  }}
}
```

y tambien posee paginacion:
```
{
  relayLinks(first: 1) {
    edges {
      node {
        id
        url
        description
        postedBy {
          id
          username
        }
      }
    }
    pageInfo {
      startCursor
      endCursor
      hasNextPage
      hasPreviousPage
    }
  }
}
```
le agregaremos mutaciones :
```python

class RelayCreateLink(graphene.relay.ClientIDMutation):
  link=graphene.Field(LinkNode)

  class Input:
    url=graphene.String()
    description=graphene.String()
  def mutate_and_get_payload(root, info,**input):
    user=info.context.user or None

    link=Link(
      url=input.get('url'),
      description=input.get('description'),
      posted_by=user,
      )
    link.save()
    return RelayCreateLink(link=link)

class RelayMutation(graphene.AbstractType):
  relay_create_link=RelayCreateLink.Field()
```

y modificamos la mutacion agregandola al schema principal
```python
class Mutation(
  users.schema.Mutation,
  links.schema.Mutation,
  links.schema_relay.RelayMutation,
  graphene.ObjectType,
  ):
  token_auth = graphql_jwt.ObtainJSONWebToken.Field()
  verify_token = graphql_jwt.Verify.Field()
  refresh_token = graphql_jwt.Refresh.Field()
```
y esto ya nos permite hacer las mutaciones:
```
mutation {
  relayCreateLink(input: 
    {url: "url introd by relay",
      description: "asda"}) {
    link {
      id
      url
      description
    }
    clientMutationId
  }
}

```
al parecer de todos modos se debe hacer las CRUDS individual y manualmente basandose en el ORM de django :/
