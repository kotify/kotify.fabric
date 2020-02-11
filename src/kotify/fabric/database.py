from . import aws, docker
from ._core import Collection, local, task


@task
def reset(c):
    local("django-admin reset_db --noinput -c")


def get_namespace(use_aws=False, use_docker=False):
    ns = Collection("db")
    ns.add_task(reset)
    if use_aws:
        ns.add_task(aws.database_dump)
    if use_docker:
        ns.add_task(docker.pg_restore)
    return ns
