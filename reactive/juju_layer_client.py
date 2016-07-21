import os
import subprocess
from subprocess import check_call

from charms.reactive import when, when_not, set_state
from charmhelpers.core import hookenv
from charmhelpers.fetch import add_source, apt_update, apt_install


@when_not('juju-agent.installed')
def install_juju_client():
    add_source('ppa:juju/devel')
    apt_update()
    apt_install(['juju'])
    set_state('juju-agent.installed')


@when('config.changed')
def config_changed():
    config = hookenv.config()
    if config.changed('juju-api-nonce'):
        register(config.get('juju-api-nonce'))
        set_state('juju-agent.registered')


@when_not('juju-agent.registered'):
def not_registered():
    hookenv.status_set('blocked', 'authenticate with "juju auth-agent %s"' % (hookenv.service_name()))


def new_password():
    return ''.join([random.choice(string.printable) for _ in range(20)])


def register(nonce):
    agent_name = hookenv.local_unit().replace('/', '-')
    agent_password = new_password()
    env = {}
    env.update(os.environ)
    env['HOME'] = hookenv.charm_dir()
    with Popen(['juju', 'register', nonce], universal_newlines=True, stdin=PIPE) as p:
        p.communicate(input="""
%(name)s
%(password)s
%(password)s
""" % {name: agent_name, password: agent_password})
    hookenv.status_set('active', 'agent %s authenticated' % (hookenv.service_name()))
