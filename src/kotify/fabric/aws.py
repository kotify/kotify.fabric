import pathlib

from ._core import Collection, local, task


def mssh_args(c):
    return f"-r {c.aws.region} -o IdentitiesOnly=yes {c.user}@{c.aws.instance_id}"


@task(default=True)
def mssh(c):
    local(f"mssh {mssh_args(c)}", pty=True)


@task
def addkey(c):
    local(
        f"aws ec2-instance-connect send-ssh-public-key \
            --region {c.aws.region} \
            --instance-id {c.aws.instance_id} \
            --availability-zone {c.aws.availability_zone} \
            --instance-os-user {c.user} \
            --ssh-public-key file://~/.ssh/id_rsa.pub",
        hide="out",
    )


@task(name="dump")
def database_dump(c):
    local_dump = pathlib.Path(c.get("database", {}).get("local_dump", "dump.db"))
    local(f"mssh {mssh_args(c)} -- 'sudo -u {c.server.user} -i -- app-db-dump'")
    local(f"msftp {mssh_args(c)}:{c.server.home_dir}/{local_dump.name} {local_dump}")


ns = Collection("ssh")
ns.add_task(mssh)
ns.add_task(addkey)
