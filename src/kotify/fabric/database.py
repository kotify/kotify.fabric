import os
import pathlib

import invoke.exceptions

from . import aws, docker
from ._core import Collection, local, task


@task(name="restore")
def pg_restore(c):
    code_path = pathlib.Path(c.get("docker", {}).get("workdir", "/code"))
    local_dump = c.get("database", {}).get("local_dump", "dump.db")
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
            {code_path} / {local_dump}"
    )
    post_restore_script = c.get("database", {}).get("post_restore_script")
    if post_restore_script:
        local(f"psql --dbname={database_url} -f {post_restore_script}")


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
    else:
        ns.add_task(pg_restore)
    return ns
