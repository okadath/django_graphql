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

mutation my{
  createCategory(name:"as"){
    name
  }
}