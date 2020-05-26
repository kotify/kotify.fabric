import pathlib

from ._config import Config
from ._core import Collection, local, task


@task(name="restore")
def pg_restore(c):
    """Restore postgresql database from dump."""
    code_path = pathlib.Path(c.get("docker", {}).get("workdir", "/code"))
    config = Config(c)
    local(
        f'docker-compose exec -u postgres db bash -c "\
            pg_restore \
                --dbname=\\$DATABASE_URL \
                --schema=public \
                --no-privileges \
                --no-owner \
                --clean \
                --if-exists \
                {code_path / config.database_local_dump} \
        "',
        pty=True,
    )
    if config.post_restore_script:
        local(
            f'docker-compose exec -u postgres db bash -c "\
                psql \
                    --dbname=\\$DATABASE_URL \
                    -f {code_path / config.post_restore_script} \
            "',
            pty=True,
        )


@task(name="minimal")
def docker_minimal(c):
    """Up docker services from fabric.yml:docker.minimal."""
    local(f"docker-compose up --no-deps {' '.join(c.docker.minimal)}")


@task(name="main", default=True)
def docker_main(c):
    """Up docker services from fabric.yml:docker.main."""
    local(f"docker-compose up --no-deps {' '.join(c.docker.main + c.docker.minimal)}")


@task(name="all")
def docker_all(c):
    """Up docker services."""
    local("docker-compose up")


ns = Collection("docker")
ns.add_task(docker_minimal)
ns.add_task(docker_main)
ns.add_task(docker_all)
