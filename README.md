# UE-AD-A1-REST

TP de réalisation d'une application backend avec une architecture microservices en Python.

## Services

Chaque service possède son propre fichier `README.md` dans son dossier respectif, cette section a pour objectif de les lister avec leur objectif.

- user : Gère le registre des utilisateurs et leurs permissions
- movie : Gère le catalogue de films et d'acteurs
- schedule : Gère les séances de visionnage 
- booking : Gère les réservations aux séances

Le schéma ci-dessous détaille les échange entre les différents services :

> `# TODO: insert image`

## Docker

Chaque service possède un Dockerfile permettant de le lancer dans un conteneur.

Par souci de practicité, deux fichiers permettent de lancer l'ensemble des services à l'aide de Docker Compose :
- `docker-compose.yml` : Les services utilisent chacun leur(s) fichiers json respectifs pour stocker les données
- `docker-compse-mongo.yml` : Les services utilisent une instance de MongoDB commune lancée dans un conteneur aux côtés des services

Pour démarrer les services :
```sh
# Version JSON
docker compose -f docker-compose.yml up --build

# Version MongoDB
docker compose -f docker-compose-mongo.yml up --build
``` 