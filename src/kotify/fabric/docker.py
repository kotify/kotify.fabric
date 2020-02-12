import pathlib

from ._core import Collection, local, task


@task(name="restore")
def pg_restore(c):
    code_path = pathlib.Path(c.get("docker", {}).get("workdir", "/code"))
    local_dump = c.get("database", {}).get("local_dump", "dump.db")
    local(
        f'docker-compose exec -u postgres db bash -c "\
            pg_restore \
                --dbname=\\$DATABASE_URL \
                --schema=public \
                --no-privileges \
                --no-owner \
                --clean \
                --if-exists \
                {code_path / local_dump} \
        "',
        pty=True,
    )
    post_restore_script = c.get("database", {}).get("post_restore_script")
    if post_restore_script:
        local(
            f'docker-compose exec -u postgres db bash -c "\
                psql \
                    --dbname=\\$$DATABASE_URL \
                    -f {code_path / post_restore_script} \
            "'
        )


@task(name="minimal")
def docker_minimal(c):
    local(f"docker-compose up --no-deps {' '.join(c.docker.minimal)}")


@task(name="up")
def docker_up(c):
    local(f"docker-compose up")


@task(name="down")
def docker_down(c):
    local(f"docker-compose down")


@task(name="build")
def docker_build(c):
    local(f"docker-compose build")


ns = Collection("docker")
ns.add_task(docker_minimal)
ns.add_task(docker_up)
ns.add_task(docker_down)
ns.add_task(docker_build)
