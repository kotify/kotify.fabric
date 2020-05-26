import datetime
import os
import pathlib

import invoke.exceptions

from . import aws, docker
from ._config import Config
from ._core import Collection, local, task

FABRIC_USE_AWS = os.environ.get("FABRIC_USE_AWS", False)
FABRIC_USE_DOCKER = os.environ.get("FABRIC_USE_DOCKER", False)


@task(name="restore")
def pg_restore(c, database_url=None):
    """Restore database from dump."""
    config = Config(c)
    database_url = database_url or os.environ.get("DATABASE_URL")
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
    if config.post_restore_script:
        local(f"psql --dbname={database_url} -f {config.post_restore_script}")


@task
def reset(c):
    """Reset database using django-extensions `reset_db`."""
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


ns = Collection("db")
ns.add_task(reset)
if FABRIC_USE_AWS:
    ns.add_task(aws.database_dump)
if FABRIC_USE_DOCKER:
    ns.add_task(docker.pg_restore)
else:
    ns.add_task(pg_restore)
