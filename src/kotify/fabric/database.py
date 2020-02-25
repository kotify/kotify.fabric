import datetime
import os
import pathlib

import invoke.exceptions

from . import aws
from . import docker as _docker
from ._config import Config
from ._core import Collection, local, task


@task(name="pg_restore")
def pg_restore(c):
    """Restore database from dump"""
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
    """Restore database from dump (tries local restore then in docker)"""
    if host:
        try:
            pg_restore(c)
        except invoke.exceptions.Failure:
            pass
    if docker:
        _docker.pg_restore(c)


@task
def reset(c):
    """Reset database using django-extensions `reset_db`"""
    local("django-admin reset_db --noinput -c")


def create_dump(c):
    try:
        local_dump = pathlib.Path(c["database"]["local_dump"]).absolute()
    except KeyError:
        local_dump = pathlib.Path("dump/dump.db")
    dump_dir = local_dump.parent
    dump_name = local_dump.name
    ts = datetime.datetime.now().strftime("%F-%H:%M:%S")
    ts_path = dump_dir / ("_" + ts).join(os.path.splitext(dump_name))
    if not dump_dir.exists():
        dump_dir.mkdir(parents=True)
    c.run(f"sudo -u {c.server.user} -i -- app-db-dump")
    local(
        f"rsync --archive --compress --progress {c.host}:{c.server.home_dir}/{dump_name} {ts_path}"
    )
    local(f"ln -f -s {ts_path.name} {local_dump}")


def get_namespace(use_aws=False):
    ns = Collection("db")
    ns.add_task(reset)
    if use_aws:
        ns.add_task(aws.database_dump)
    ns.add_task(restore)
    return ns
