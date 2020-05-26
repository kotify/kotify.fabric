from kotify.fabric import Collection, aws, database, docker, task
from kotify.fabric.deploy import BackendDeploy, FrontendDeploy


@task(name="frontend")
def frontend(c, release=True, install=True):
    deploy = FrontendDeploy(c, release=release)
    if install:
        deploy.node.install()


@task(aws.addkey, hosts=["kotify.invalid"], name="backend")
def backend(c):
    deploy = BackendDeploy(c)
    deploy.python.install()


@task(frontend, backend, default=True, name="deploy")
def deploy(c):
    pass


d = Collection("deploy")
d.add_task(deploy)
d.add_task(frontend)
d.add_task(backend)


ns = Collection()
ns.add_collection(d)
ns.add_collection(database.ns)
ns.add_collection(aws.ns)
ns.add_collection(docker.ns)
