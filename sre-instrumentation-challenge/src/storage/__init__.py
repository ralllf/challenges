from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
from storage.bucket import bucket_blueprint

app = Flask(__name__, static_url_path="", static_folder="../static")
app.config.from_object(__name__)

metrics = PrometheusMetrics(app, group_by="endpoint")
metrics.info("app_info", "Application info", version="0.1.0")
app.register_blueprint(bucket_blueprint, url_prefix="/api")