import pathlib

from ._config import Config
from ._core import Collection, local, task


@task(name="restore")
def pg_restore(c):
    """Restore postgresql database from dump"""
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
    post_restore_script = c.get("database", {}).get("post_restore_script")
    if post_restore_script:
        local(
            f'docker-compose exec -u postgres db bash -c "\
                psql \
                    --dbname=\\$DATABASE_URL \
                    -f {code_path / post_restore_script} \
            "',
            pty=True,
        )


@task(name="minimal")
def docker_minimal(c):
    """Up docker services from fabric.yml:docker.minimal"""
    local(f"docker-compose up --no-deps {' '.join(c.docker.minimal)}")


@task(name="up")
def docker_up(c):
    """Up docker services"""
    local("docker-compose up")


@task(name="down")
def docker_down(c):
    """Down docker services"""
    local("docker-compose down")


@task(name="build")
def docker_build(c):
    """Build docker"""
    local("docker-compose build")


ns = Collection("docker")
ns.add_task(docker_minimal)
ns.add_task(docker_up)
ns.add_task(docker_down)
ns.add_task(docker_build)
