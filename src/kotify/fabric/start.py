import os

from . import docker, procfile

FABRIC_USE_DOCKER = os.environ.get("FABRIC_USE_DOCKER", False)


if FABRIC_USE_DOCKER:
    ns = docker.ns
else:
    ns = procfile.ns
