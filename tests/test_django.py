from kotify.fabric.deploy import DjangoController


def test_get_cmd(fake_deploy):
    assert DjangoController._get_cmd("migrate") == "django-admin migrate --noinput"
    assert (
        DjangoController._get_cmd("migrate", settings="settings.prod")
        == "django-admin migrate --noinput --settings settings.prod"
    )


def test_django(fake_deploy):
    dc = DjangoController(fake_deploy)
    dc.migrate()
    assert fake_deploy._runs == [
        {"cmd": "django-admin migrate --noinput", "msg": "django migrate"}
    ]
    fake_deploy.reset_fake()
    dc.collectstatic(settings="path.to.settings")
    assert fake_deploy._runs == [
        {
            "cmd": "django-admin collectstatic --noinput --settings path.to.settings",
            "msg": "django collectstatic",
        }
    ]
