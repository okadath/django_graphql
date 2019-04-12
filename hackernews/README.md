```
 pip install django-filter
 pip install django-graphql-jwt
```

```
python manage.py startapp links
 python manage.py makemigrations
 python manage.py migrate
 ``` 
en  python manage.py shell:
```python
>>> from links.models import Link
>>> Link.objects.create(url='https://www.howtographql.com/', description='The Fullstack Tutorial for GraphQL')
<Link: Link object (1)>
>>> Link.objects.create(url='https://twitter.com/jonatasbaldin/', description='The Jonatas Baldin Twitter')
<Link: Link object (2)>
>>> 
```
 en link/schema.py:
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
en hackernews/hackernews/schema.py:

```python
import graphene
import links.schema

class Query(links.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)

```

y crear en hackernews/hackernews/urls.py
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


luego creamos en el schema las mutaciones:
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
y en el schema de la app principal:
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
creamos una carpeta users y ahi un schema.py usando el modelo de usuarios de django:
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


en la carpeta hackernews/hackernews.py:
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

para ahcer querys de los usuarios agregar al users/schema.py:
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



