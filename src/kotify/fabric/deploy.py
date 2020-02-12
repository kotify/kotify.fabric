import datetime
import pathlib
import random
import string
import tempfile

import invoke.exceptions

from ._core import local


class TermColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class BaseController:
    def __init__(self, deploy):
        self.deploy = deploy


class PipPipfilePythonController(BaseController):
    def install(self):
        self.deploy.run("PIPENV_VERBOSITY=-1 pipenv lock -r > _req.txt")
        self.deploy.run("pip install -r _req.txt", msg="pip install")
        self.deploy.run("rm _req.txt")


class DjangoController(BaseController):
    def collectstatic(self):
        self.deploy.run(
            "django-admin collectstatic --noinput", msg="django-admin collectstatic"
        )

    def migrate(self):
        self.deploy.run("django-admin migrate --noinput", msg="migrate db")


class SupervisorController(BaseController):
    def __init__(self, deploy, services, pre_stop_services=None):
        super().__init__(deploy)
        self.services = services
        self.pre_stop_services = pre_stop_services

    def stop_app(self):
        self._pre_stop()
        if self.services:
            services = " ".join(self.services)
        self.deploy.sudo(f"supervisorctl stop {services}", msg=f"stop {services}")

    def _pre_stop(self):
        if self.pre_stop_services:
            services = " ".join(self.pre_stop_services)
            self.deploy.sudo(f"supervisorctl stop {services}", msg=f"stop {services}")

    def start_app(self):
        if self.services:
            services = " ".join(self.services)
        self.deploy.sudo(f"supervisorctl start {services}", msg=f"start {services}")
        self._post_start()

    def _post_start(self):
        if self.pre_stop_services:
            services = " ".join(self.pre_stop_services)
            self.deploy.sudo(f"supervisorctl start {services}", msg=f"start {services}")


class GitController(BaseController):
    def __init__(self, deploy, url, release_branch, project_dir):
        super().__init__(deploy)
        self.url = url
        self.release_branch = release_branch
        self.project_dir = pathlib.Path(project_dir)

    def is_repo_exist(self):
        if (self.project_dir / ".git").exists():
            return True
        if self.project_dir.exists():
            raise invoke.exceptions.Exit(
                "Project directory exists but it's not a git repo."
            )
        return False

    def is_url_match(self):
        result = self.deploy.run("git remote show origin -n")
        try:
            url = next(
                s for s in result.stdout.split("\n") if s.startswith("Fetch URL: ")
            )[11:]
        except StopIteration:
            raise invoke.exceptions.Exit(
                f"`git remote show origin -n` returns invalid response:\n{result.stdout}"
            )
        if url != self.url:
            self.deploy.run(
                "git remote set-url origin {self.url}", msg="update git url"
            )

    def pull(self, version=None):
        if self.is_repo_exist:
            if not self.is_url_match:
                self.deploy.run(
                    f"git remote set-url origin {self.url}",
                    msg="update remote origin url",
                )
            self.deploy.run(f"git fetch origin {self.release_branch}", msg="git pull")
        else:
            self.deploy.sudo(
                f"git clone {self.url} {self.project_dir}",
                user=self.user,
                msg="git clone",
            )
        self.deploy.run(f"git checkout --force {version or self.release_branch}")


class BaseDeploy:
    RANDOM_CHARS = f"{string.ascii_letters}{string.digits}_"

    def __init__(self, context):
        self.context = context
        env_bin = context.server.virtualenv_dir + "/bin"
        self._cmd_prefix = (
            f"source {env_bin}/activate && cd {context.server.project_dir}"
        )

    def sudo(self, cmd, msg=None, user="root"):
        if msg:
            print("*" * 80)
            print(TermColors.OKGREEN + msg + TermColors.ENDC)
            print("\n")
        result = self.context.sudo(f'bash -c "{cmd}"', user=user, hide=True, warn=True)
        if result.exited:
            print(TermColors.FAIL + result.stderr + TermColors.ENDC)
            raise invoke.exceptions.Exit("Command returned non zero code.")
        return result

    def run(self, cmd, msg=None):
        return self.sudo(
            f"{self._cmd_prefix} && {cmd}", msg=msg, user=self.context.server.user
        )

    def put(self, src, dst, msg=None):
        tmp_name = f"{tempfile.gettempdir()}/{self.gen_random_string(8)}"
        user = self.context.server.user
        self.context.put(src, tmp_name)
        self.sudo(f"mv {tmp_name} {dst} && chown {user}:{user} {dst}", msg=msg)

    def rsync(self, src, dst, msg=None):
        user = self.context.server.user
        if msg:
            print("*" * 80)
            print(TermColors.OKGREEN + msg + TermColors.ENDC)
            print("\n")
        local(
            f'rsync \
                --archive \
                --compress \
                --delay-updates \
                --delete-after \
                --owner \
                --group \
                --chown={user}:{user} \
                --rsync-path="sudo rsync" \
                {src} {self.context.host}:{dst} \
            '
        )

    @classmethod
    def gen_random_string(cls, size):
        return "".join(random.choice(cls.RANDOM_CHARS) for _ in range(size))


class BackendDeploy(BaseDeploy):
    def __init__(self, context):
        super().__init__(context)
        self.django = DjangoController(self)
        self.python = PipPipfilePythonController(self)
        pre_stop_services = []
        if context.supervisor.celery_worker:
            pre_stop_services.append(f"celery_worker_{context.server.project_name}")
        if context.supervisor.celery_beat:
            pre_stop_services.append(f"celery_beat_{context.server.project_name}")
        self.supervisor = SupervisorController(
            self, [context.server.project_name], pre_stop_services=pre_stop_services
        )
        self.git = None
        if "git" in context:
            self.git = GitController(
                self, context.git.url, context.git.branch, context.server.project_dir
            )


class YarnController(BaseController):
    build_path = "./build"

    def __init__(self, deploy):
        super().__init__(deploy)

    def build(self, public_path):
        local(f"PUBLIC_PATH={public_path} yarn run build")
        return self.build_path

    def install(self):
        local("yarn install --frozen-lockfile")


class CloudflareCdnController(BaseController):
    def __init__(self, deploy, bucket, cdn_domain, release=True):
        super().__init__(deploy)
        self._month = datetime.datetime.now().strftime("%Y%m")
        self.cdn_domain = cdn_domain
        self.bucket = bucket
        if release:
            cdn_path = f"/build/{self._month}/"
        else:
            git_rev = local("git rev-parse --short HEAD", hide="out").stdout.strip()
            cdn_path = f"/build/ci/{git_rev}/"
        self.public_path = f"https://{self.cdn_domain}{cdn_path}"
        self.s3_path = f"s3://{self.bucket}{cdn_path}"

    def upload(self, path):
        local(
            f"aws s3 sync {path} {self.s3_path} --cache-control max-age=31536000 --acl public-read"
        )


class FrontendDeploy(BaseDeploy):
    def __init__(self, context, release=True):
        super().__init__(context)
        self.node = YarnController(self)
        if context.aws and context.aws.cdn_domain:
            self.cdn = CloudflareCdnController(
                self, context.aws.bucket, context.aws.cdn_domain, release=release
            )
