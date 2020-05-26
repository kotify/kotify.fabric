from ._core import Collection, local, task


@task(name="main", default=True)
def start_main(c):
    local(f"overmind start -l {','.join(c.start.main + c.start.minimal)}", pty=True)


@task(name="minimal")
def start_minimal(c):
    local(f"overmind start -l {','.join(c.start.minimal)}", pty=True)


@task(name="all")
def start_all(c):
    local("overmind start", pty=True)


ns = Collection("start")
ns.add_task(start_all)
ns.add_task(start_main)
ns.add_task(start_minimal)
