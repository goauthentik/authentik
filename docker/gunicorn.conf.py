import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
wsgi_app = "passbook.root.asgi:application"

user = "passbook"
group = "passbook"

worker_class = "uvicorn.workers.UvicornWorker"
