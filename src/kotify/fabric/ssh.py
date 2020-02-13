import pathlib

from paramiko.hostkeys import HostKeyEntry, HostKeys

from ._core import local


def prepare_ssh(c, gen_key=True):
    ssh = pathlib.Path("~/.ssh").expanduser()
    if not ssh:
        local("mkdir ~/.ssh")
        local("chmod 700 ~/.ssh")
    if gen_key:
        id_rsa = ssh / "id_rsa"
        if not id_rsa.exists():
            local(f'ssh-keygen -b 2048 -t rsa -f {id_rsa} -q -N ""')
    if c.server.get("host_key"):
        hk = HostKeys(ssh / "known_hosts" if (ssh / "known_hosts").exists() else None)
        if not hk.lookup(c.host):
            host_key = HostKeyEntry.from_line(f"{c.host} {c.server.host_key}")
            assert host_key, "Invalid value in fabric.yml server.host_key"
            hk.add(",".join(host_key.hostnames), host_key.key.get_name(), host_key.key)
            hk.save(ssh / "known_hosts")
