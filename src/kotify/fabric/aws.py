import datetime
import json
import os.path
import pathlib

from ._core import Collection, local, task


def mssh_args(c):
    return f"-r {c.aws.region} -o IdentitiesOnly=yes {c.user}@{c.aws.instance_id}"


def get_secret(region_name, secret_id, plain=False):
    import boto3

    client = boto3.client(service_name="secretsmanager", region_name=region_name)
    secret = client.get_secret_value(SecretId=secret_id)["SecretString"]
    return secret if plain else json.loads(secret)


def populate_env_from_secret(region_name, secret_id):
    """
    Add environment variables from AWS secret.

    It doesn't overwrite existing variables.
    """
    for name, value in get_secret(region_name, secret_id).items():
        os.environ.setdefault(name, value)


@task(default=True)
def mssh(c):
    """
    SSH into production server (using AWS access key).

    Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY variables in environment.
    """
    local(f"mssh {mssh_args(c)}", pty=True)


@task
def addkey(c):
    """Add your id_rsa.pub to the production server for 60 seconds."""
    local(
        f"aws ec2-instance-connect send-ssh-public-key \
            --region {c.aws.region} \
            --instance-id {c.aws.instance_id} \
            --availability-zone {c.aws.availability_zone} \
            --instance-os-user {c.user} \
            --ssh-public-key file://~/.ssh/id_rsa.pub",
        hide="out",
    )


@task(addkey)
def host(c):
    """Return `username@hostname` that can be used in ssh."""
    import boto3

    ec2 = boto3.client("ec2", region_name=c["aws"]["region"])
    instances = ec2.describe_instances(InstanceIds=[c["aws"]["instance_id"]])
    host = instances["Reservations"][0]["Instances"][0]["PublicDnsName"]
    print(f"{c['user']}@{host}")


@task(name="dump")
def database_dump(c):
    """
    Create database dump (using AWS access key).

    Requires AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY variables in environment.
    """
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
ns.add_task(host)
