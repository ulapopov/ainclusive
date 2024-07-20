from app import app as application

if __name__ == "__main__":
    from gunicorn.app.base import BaseApplication


    class FlaskApp(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            for key, value in self.options.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key, value)

        def load(self):
            return self.application


    # Run Gunicorn
    options = {
        'bind': f"0.0.0.0:5001",
        'workers': 2,
        'worker_class': 'sync',
        'threads': 2,
        'loglevel': 'info',
        'timeout': 0,
        'max_requests': 0,
    }
    flask_app = FlaskApp(application, options)
    flask_app.run()
