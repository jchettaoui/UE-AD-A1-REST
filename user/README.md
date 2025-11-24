# User service

## Service description

Ce service permet de gérer les connexions des utlisateurs

- admin :  
    - CRUD sur la liste des utilisateurs
    - peut changer le statut de l'utlisateur (admin ou non)
- user : 
    - CRUD uniquement sur ses propres données.
    - accès à la lecture d'un utilisateur par id
    - peut ajouter un utilisateur
    - peut voir si un utilisateur est admin

## Requirements

- Python
- Docker (if you want to run it inside a container)

## Description des flags

- `-j` : Importer la base depuis un fichier Json
- `-m` : Importe la base avec MongoDB
- `--storage` : Specifier l'endroit ou se trouve la base à importer, si rien n'est précisé, une destination par défaut est        utilisée

## Standalone

Lancer sans docker 

```sh
# Installation
pip install -r requirements.txt

# Start app
python user.py < -j | -m > [--storage ...]
```

## Docker

Lancer avec docker

```sh
# Build image
docker build . -t user-service

# Start container with either json or mongo as data storage
docker run --name user-service -d user-service:latest < -j | -m > [--storage ...]
```