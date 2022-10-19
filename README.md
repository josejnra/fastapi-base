## FastAPI Base project

### Run Locally
To easily run this application locally it's recommended to use the [remote container extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for vscode. Then, just run:
```shell
uvicorn app.main:app --host 0.0.0.0 --port 8000
# or
npm run app
```
The application should be available at [0.0.0.0:8000](http://0.0.0.0:8000).
