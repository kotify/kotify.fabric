from kotify.fabric.deploy import DjangoController


def test_get_cmd(fake_deploy):
    assert (
        DjangoController._get_cmd("migrate", options=["--noinput"])
        == "django-admin migrate --noinput"
    )
    assert (
        DjangoController._get_cmd("migrate", settings="settings.prod")
        == "django-admin migrate --settings settings.prod"
    )


def test_django(fake_deploy):
    dc = DjangoController(fake_deploy)
    dc.migrate()
    assert fake_deploy._runs == [
        {"cmd": "django-admin migrate --noinput", "msg": "django-admin migrate"}
    ]
    fake_deploy.reset_fake()
    dc.collectstatic(settings="path.to.settings")
    assert fake_deploy._runs == [
        {
            "cmd": "django-admin collectstatic --noinput --settings path.to.settings",
            "msg": "django-admin collectstatic",
        }
    ]


def test_run(fake_deploy):
    dc = DjangoController(fake_deploy)
    dc.run("customcommand")
    assert fake_deploy._runs == [
        {"cmd": "django-admin customcommand", "msg": "django-admin customcommand"}
    ]
    fake_deploy.reset_fake()
    dc.run("customcommand", options=["--option=a"])
    assert fake_deploy._runs == [
        {
            "cmd": "django-admin customcommand --option=a",
            "msg": "django-admin customcommand",
        }
    ]
