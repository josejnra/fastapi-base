## FastAPI Base project

### Run Locally
To easily run this application locally it's recommended to use the [remote container extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for vscode. Then, just run:
```shell
docker-compose up -d
```
The application should be available at [0.0.0.0:8000](http://0.0.0.0:8000).


### Migrations

#### Init alembic
```shell
alembic init migrations
```

#### Create migration
```shell
alembic revision --autogenerate -m "create tables first version"
```

#### Run migrations
```shell
alembic upgrade head
```
