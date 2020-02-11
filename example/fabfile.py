import kotify.fabric.aws
import kotify.fabric.database
import kotify.fabric.docker
from kotify.fabric import Collection, task
from kotify.fabric.deploy import BackendDeploy, FrontendDeploy


@task(name="frontend")
def frontend(c, release=True, install=True):
    deploy = FrontendDeploy(c, release=release)
    if install:
        deploy.node.install()


@task(kotify.fabric.aws.addkey, hosts=["kotify.invalid"], name="backend")
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
ns.add_collection(kotify.fabric.database.get_namespace(use_aws=True, use_docker=True))
ns.add_collection(kotify.fabric.aws.ns)
ns.add_collection(kotify.fabric.docker.ns)
