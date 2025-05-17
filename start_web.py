# run_dev.py
import subprocess
import time
import os

PROJECT_NAME = "davtj_web"  # Change to your actual project name

def start_celery():
    print("Starting Celery worker...")
    return subprocess.Popen([
        "celery", "-A", PROJECT_NAME, "worker", "--loglevel=info"
    ])

def start_django():
    print("Starting Django dev server...")
    return subprocess.Popen(["python3", "manage.py", "runserver"])

if __name__ == "__main__":
    try:
        celery_proc = start_celery()
        time.sleep(1)  # Give Celery a second to connect

        django_proc = start_django()

        django_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for proc in [celery_proc]:
            if proc:
                proc.terminate()