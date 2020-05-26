import os
import pathlib

from paramiko.hostkeys import HostKeyEntry, HostKeys

from . import aws
from ._core import Collection, local, task

FABRIC_USE_AWS = os.environ.get("FABRIC_USE_AWS", False)


def _create_keys_known_hosts(context, gen_key):
    ssh = pathlib.Path("~/.ssh").expanduser()
    if not ssh:
        local("mkdir ~/.ssh")
        local("chmod 700 ~/.ssh")
    if gen_key:
        id_rsa = ssh / "id_rsa"
        if not id_rsa.exists():
            local(f'ssh-keygen -b 2048 -t rsa -f {id_rsa} -q -N ""')
    if context.server.get("host_key"):
        hk = HostKeys(ssh / "known_hosts" if (ssh / "known_hosts").exists() else None)
        host = getattr(context, "host", None)
        if host and not hk.lookup(host):
            host_key = HostKeyEntry.from_line(f"{host} {context.server.host_key}")
            assert host_key, "Invalid value in fabric.yml server.host_key"
            hk.add(",".join(host_key.hostnames), host_key.key.get_name(), host_key.key)
            hk.save(ssh / "known_hosts")


@task
def prepare(context, gen_key=True):
    """Prepare ssh keys to connect to remote host."""
    _create_keys_known_hosts(context, gen_key=gen_key)
    if FABRIC_USE_AWS:
        aws.addkey(context)


ns = Collection("ssh")
ns.add_task(prepare)
if FABRIC_USE_AWS:
    ns.add_task(aws.mssh)
    ns.add_task(aws.addkey)
    ns.add_task(aws.host)
