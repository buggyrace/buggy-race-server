release: flask db upgrade
web: gunicorn buggy_race_server.app:app -b 0.0.0.0:$PORT -w 3 --timeout 60
