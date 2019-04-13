### Tuto oficial
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

## jwt

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














