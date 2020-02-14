import os

import invoke.exceptions

from . import aws
from . import docker as _docker
from ._config import Config
from ._core import Collection, local, task


@task(name="pg_restore")
def pg_restore(c):
    config = Config(c)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise invoke.exceptions.Exit("DATABASE_URL environment variable is not set.")
    local(
        f"pg_restore \
            --dbname={database_url} \
            --schema=public \
            --no-privileges \
            --no-owner \
            --clean \
            --if-exists \
            {config.database_local_dump}"
    )
    post_restore_script = c.get("database", {}).get("post_restore_script")
    if post_restore_script:
        local(f"psql --dbname={database_url} -f {post_restore_script}")


@task(name="restore")
def restore(c, host=True, docker=True):
    if host:
        try:
            pg_restore(c)
        except invoke.exceptions.Failure:
            pass
    if docker:
        _docker.pg_restore(c)


@task
def reset(c):
    local("django-admin reset_db --noinput -c")


def get_namespace(use_aws=False):
    ns = Collection("db")
    ns.add_task(reset)
    if use_aws:
        ns.add_task(aws.database_dump)
    ns.add_task(restore)
    return ns
