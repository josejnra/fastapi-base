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
alembic init -t async alembic
```

#### Create migration
```shell
# against database
alembic revision --autogenerate -m "create tables first version"
# no database required, but requires to manually edit script generated
alembic revision -m "add last_name to actor"
```

### Observability
This application uses [opentelemetry](https://opentelemetry.io/) to provide observability with manually instrumented code and [opentelemetry collector](https://opentelemetry.io/docs/collector/about/).

#### Traces
Check the traces at [http://localhost:9411](http://localhost:9411) or [grafana](http://localhost:3000/) on data source `Tempo`


#### Metrics
Check the metrics at [http://localhost:8889/metrics](http://localhost:8889/metrics)
or [grafana](http://localhost:3000/) on data source `Prometheus`

#### Logs
Check the metrics at [grafana](http://localhost:3000/) on data source `Loki`

#### Run migrations
```shell
alembic upgrade head
```
