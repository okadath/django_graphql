
typeMutation {
	agregarCurso(
		descripcion: String,
		profesorId: String
	): Curso
}

paso de variables
curso (id=1) {
	...
}
## fragments
puedes crear un fragment con los campos que mas se 
solicita en las peticiones y si en alguna peticion necesitas mas campos de los que hay en el fragment puedes hacerlo.

Ejemplo

fragment base onCourse {
	id: ID!
	titulo: String!
	descripcion: String!
	profesor: Profesor
	rating: Float
}
y lo usarias de esta forma

query {
	courses {
		...base
	}
}
y si en otra peticion necesitas mas campos de los que estan declarados en el fragment seria

query {
	courses {
		...base
		comentarios: [Comentario]
	}
}
De esta forma podemos tener definidos los campos que mas se soliciten en las peticiones
y complementarlos cuando necesitemos mas.

este es del capitulo

{
  curso(id: 1) {
    ...CamposNecesarios
  }
  cursos {
    ...CamposNecesarios
  }
}

fragment CamposNecesarios on Curso {
  titulo
  descripcion
}





##variables

definir una query con variable(si no hay valor por defecto lo quitas y ya :P)
query <nombreQuery>(<$variable>: type = <valor por defecto>) {
	curso (id=1) {
	...
  }...
}

##aliases
para evitar sobreescritura de variables
{
  cursoMasVotado: curso(id: 1) {
    titulo
    rating
  }
  cursoMasVisto: curso(id: 2) {
    titulo
    descripcion
  }
}



#inlines es para union
{
	buscar(query: 'GraphQL') {
		... on Curso {
			titulo
		}
		... on Profesor {
			nombre
		}
	}
}

#directives, para pedir condicionalmente
Existen 2 tipos:

@include incluye el campo si el argumento es true.
@skip omite el campo si el argumento es true. (revirtiendo la condición)
Declaramos la variable:

{
  "conDescription": true
}
Realizamos la consulta:

query Cursos($conDescription: Boolean!) {
  cursos {
    titulo
    descripcion @include(if: $conDescription)
  }
}


ejemplo con skip
query Cursos($conDescripcion: Boolean!, 
  					 $conProfesor: Boolean!,
             $conComentario: Boolean!) {
    cursos {
      titulo
      descripcion @include(if: $conDescripcion)  
      profesor @include(if: $conProfesor) {
        nombre
        genero
      }
      comentarios @skip(if: $conComentario) {
        nombre
      }
    }
  }
Query Variables

{
  "conDescripcion": false,
  "conProfesor": true,
  "conComentario": true
}

#mutation

Si se bajaron el proyecto, van a notar que el query de mutation de este ejemplo no van a funcionar:

mutation {
  profesorAdd(nombre: "Laura", genero: FEMENINO){
    id
  }
}
Es porque el proyecto ya trae los input types del siguiente video y funciona con el siguiente query:
mutation {
  profesorAdd(profesor: {
    nombre: "Laura"
    genero: FEMENINO
    nacionalidad: "Mexico"
  }) {
    id
  }
}
Me heché un rato tratando hacerlo funcionar (fallando miserablemente), no pierdan su tiempo como yo, solo tienen que ver el siguiente video u_u

##input types

input NuevoProfesor {
    nombre: String!
    genero: Genero
}
Consulta del lado del cliente:

mutation {
  profesorAdd(profesor: {
    nombre: "Laura"
    genero: FEMENINO
    nacionalidad: "Mexico"
  }) {
    id
  }
}
