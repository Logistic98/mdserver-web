from flask import Flask
import views

app = Flask(__name__)
app.debug = True

DEFAULT_MODULES = (
    (views.dashboard, "/"),
    (views.site, "/site"),
    (views.files, "/files"),
    (views.soft, "/soft"),
    (views.config, "/config"),
    (views.plugins, "/plugins"),
    (views.task, "/task"),
)


def setting_modules(app, modules):
    for module, url_prefix in modules:
        app.register_blueprint(module, url_prefix=url_prefix)

setting_modules(app, DEFAULT_MODULES)


if __name__ == "__main__":
    app.run()
