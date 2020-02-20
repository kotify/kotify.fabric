from kotify.fabric.deploy import SupervisorController


def test_get_services():
    assert SupervisorController._get_services([], None) == ""
    assert SupervisorController._get_services(["service_a"], None) == "service_a"
    assert SupervisorController._get_services(["service_a"], "g:") == "g:service_a"
    assert (
        SupervisorController._get_services(["service_a", "service_b"], None)
        == "service_a service_b"
    )
    assert (
        SupervisorController._get_services(["service_a", "service_b"], "gr")
        == "gr:service_a gr:service_b"
    )


def test_app(fake_deploy):
    sc = SupervisorController(fake_deploy, services=["web"])
    sc.stop_app()
    assert fake_deploy._sudos == [{"cmd": "supervisorctl stop web", "msg": "stop web"}]
    fake_deploy.reset_fake()
    sc.start_app()
    assert fake_deploy._sudos == [
        {"cmd": "supervisorctl start web", "msg": "start web"}
    ]


def test_pre(fake_deploy):
    sc = SupervisorController(
        fake_deploy, services=["web"], pre_stop_services=["service_a", "service_b"]
    )
    sc.stop_app()
    assert fake_deploy._sudos == [
        {
            "cmd": "supervisorctl stop service_a service_b",
            "msg": "stop service_a service_b",
        },
        {"cmd": "supervisorctl stop web", "msg": "stop web"},
    ]
    fake_deploy.reset_fake()
    sc.start_app()
    assert fake_deploy._sudos == [
        {"cmd": "supervisorctl start web", "msg": "start web"},
        {
            "cmd": "supervisorctl start service_a service_b",
            "msg": "start service_a service_b",
        },
    ]


def test_group(fake_deploy):
    sc = SupervisorController(
        fake_deploy, services=["web"], pre_stop_services=["service_a", "service_b"]
    )
    sc.stop_app(group="prod")
    assert fake_deploy._sudos == [
        {
            "cmd": "supervisorctl stop prod:service_a prod:service_b",
            "msg": "stop prod:service_a prod:service_b",
        },
        {"cmd": "supervisorctl stop prod:web", "msg": "stop prod:web"},
    ]
    fake_deploy.reset_fake()
    sc.start_app(group="prod")
    assert fake_deploy._sudos == [
        {"cmd": "supervisorctl start prod:web", "msg": "start prod:web"},
        {
            "cmd": "supervisorctl start prod:service_a prod:service_b",
            "msg": "start prod:service_a prod:service_b",
        },
    ]
