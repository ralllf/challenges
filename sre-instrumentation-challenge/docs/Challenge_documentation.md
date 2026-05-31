# SRE Instrumentation Challenge

This document contain all my changes i did for this challange.
The goal was to create a all in one docket compose build where we can collect and display metrics from application plus k8s deployment.

---

## 1. Add Prometheus exporter to application

To make it possible to collect metrics from the application I added a prometheus library dedicated for flask. As it build by default endpoint /metrics this is the most simple way to do it.
Please find below diff of __init__ file
### `src/storage/__init__.py`
```diff
 from flask import Flask
+from prometheus_flask_exporter import PrometheusMetrics
 from storage.bucket import bucket_blueprint

 app = Flask(__name__, static_url_path="", static_folder="../static")
 app.config.from_object(__name__)
+metrics = PrometheusMetrics(app, group_by="endpoint")
+metrics.info("app_info", "Application info", version="1.0.3")
 app.register_blueprint(bucket_blueprint, url_prefix="/api")
```

---

## 2. Builds and requirements

For the application i build a Dockerfile and requirements file. Dockerfile was build to make sure that application will be executed as user not root.
Note: Because on my local machine  port 5000 is already in sure I updated it to 5001.

### `requirements.txt`
```
flask
waitress
prometheus-flask-exporter
```

### `Dockerfile`
```diff
+FROM python:3.14-slim

+RUN useradd -m app
+USER app
+WORKDIR /home/app/app
+ENV PATH=/home/app/.local/bin:$PATH

+COPY requirements.txt ./
+RUN pip install --no-cache-dir --user -r requirements.txt
+COPY src/ ./
+EXPOSE 5001
+CMD ["python", "run.py"]
```

---

## 3. Docker compose

To make sure that challange will be achieved i added to the docker compose files section of storage_api and build a image from Dockerfile. Please be noted that better solution would be build image separate and then use it.

For the application intentionally i do not added volume. It was easier for me to make sure i created it correctly and flow exists.
### `docker-compose.yml`
```diff
   storage_api:
     build:
       context: .
     ports:
+      - 5001:5001
     environment:
+      - PORT=5001
```

Because of port adaptation i changed port in __run__ script and __prometheus__ files
### `src/run.py`
```diff
+port = os.getenv("PORT", default=5001)
```

### `deploy/prometheus/prometheus.yml`
```diff
   - job_name: "storage_api"
     scrape_interval: 10s
     static_configs:
+      - targets: ["storage_api:5001"]
```

To generate traffic correctly port in the script was updated to 5001
### `scripts/generate_traffic.sh`
```
http://localhost:5001/api/buckets/$1
```

---

## 4. Grafana

To make sure that Grafana be ready from the beginning i added a dashboard configuration by adding yaml and json files.
As this is a "dev" environment and is dynamic I added a fix uid for datasource configuration as well as in the dashboard configuration to make sure there will be no implication with IDs.
I believe i had issue with correct IDs because of using a Chrome browse and after restarts i got No Datasource Found.
### `deploy/grafana/provisioning/datasources/datasource.yaml`
```diff
 datasources:
   - name: Prometheus
+    uid: prometheus
     type: prometheus
     access: proxy
     url: http://prometheus:9090
```

The dashboard was build in Grafana UI and then exported as json file. To make sure it will work i had to remove section of "__inputs__" to make sure that will work after each provisioning.
 
---
## Kubernetes deployment

To build a k8s deployment configuration i use a took called kompose.
Generated files required some updates to make sure it will be usable on k8s but make it way faster to create.
Additionally i created a Configmaps which were not created by kompose and save there configuration of Grafana and Prometheus.
I tested this on minikube. It is required to build an image of storage-api first.
Files can you found in **`deploy/k8s`**

---

## What i found

- **`deleteDatasources` in `datasource.yaml`**
	- On every restart Grafana deletes and recreates the Prometheus datasource, so its numeric `id` keeps climbing (verified: 2 → 3 → 4 across restarts). This is harmless because the dashboard references the datasource by a fixed `uid: prometheus` (set in `datasource.yaml`), which stays stable - panels always resolve. The only symptom is that an already-open browser tab still holding the old numeric id shows "invalid data source" until a hard refresh (Cmd+Shift+R). Kept as in the original; the fixed `uid` is what makes it safe.
- **`code 500 in responses`**
	- looks this was an intentional. This is a fake code for DELETE request and set manually in the code.
