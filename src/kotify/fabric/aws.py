import datetime
import os.path
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
    local_dump = pathlib.Path(
        c.get("database", {}).get("local_dump", "dump/dump.db")
    ).absolute()
    dump_dir = local_dump.parent
    dump_name = local_dump.name
    ts = datetime.datetime.now().strftime("%F-%H:%M:%S")
    ts_path = dump_dir / ("_" + ts).join(os.path.splitext(dump_name))
    if not dump_dir.exists():
        dump_dir.mkdir(parents=True)
    local(f"mssh {mssh_args(c)} -- 'sudo -u {c.server.user} -i -- app-db-dump'")
    local(f"msftp {mssh_args(c)}:{c.server.home_dir}/{dump_name} {ts_path}")
    local(f"ln -f -s {ts_path.name} {local_dump}")


ns = Collection("aws")
ns.add_task(mssh)
ns.add_task(addkey)
