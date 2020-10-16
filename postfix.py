#!/usr/bin/python
import subprocess


DOCUMENTATION = '''
---
module: postfix
short_description: changes postfix configuration parameters
description:
  - The M(postfix) module changes postfix configuration by invoking 'postconf'.
    This is needed if you don't want to use M(template) for the entire main.cf,
    because M(lineinfile) cannot handle multi-line configuration values, and
    solutions involving M(command) are cumbersone or don't work correctly
    in check mode.
  - Be sure to run C(postfix reload) (or, for settings like inet_interfaces,
    C(service postfix restart)) afterwards.
options:
  name:
    description:
      - the name of the setting
    required: true
    default: null
  value:
    description:
      - the value for that setting
    required: true
    default: null
  path:
    description:
      - put the desired setting in this postfix configuration directory (d: /etc/postfix)
author:
  - Marius Gedminas <marius@pov.lt>
'''

EXAMPLES = '''
- postfix: name=myhostname value={{ ansible_fqdn }}

- postfix: name=mynetworks value="127.0.0.0/8, [::1]/128, 192.168.1.0/24"

- postfix: name={{ item.name }} value="{{ item.value }}"
  with_items:
    - { name: inet_interfaces, value: loopback-only }
    - { name: inet_protocols,  value: ipv4          }
'''


def run(args, module):
    try:
        cmd = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = cmd.communicate()
        rc = cmd.returncode
    except (OSError, IOError) as e:
        module.fail_json(rc=e.errno, msg=str(e), cmd=args)
    if rc != 0:
        module.fail_json(rc=rc, msg=err, cmd=args)
    if err:
        module.warn(str(err))
    return out


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            value=dict(required=True),
            path=dict(type='path', default='/etc/postfix', required=False),
        ),
        supports_check_mode=True,
    )
    name = module.params['name']
    value = module.params['value'].strip()
    cfgpath = module.params['path'].strip()
    old_value = run(['postconf', '-c', cfgpath, '-h', name], module).decode("utf-8").strip()
    if value == old_value:
        module.exit_json(
            msg="",
            changed=False,
        )
    if not module.check_mode:
        run(['postconf', '-c', cfgpath, '{}={}'.format(name, value)], module)
    module.exit_json(
        msg="setting changed",
        diff=dict(
            before_header='postconf -c {} -h {}'.format(cfgpath, name),
            after_header='postconf -c {} -h {}'.format(cfgpath, name),
            before=old_value + '\n',
            after=value + '\n'),
        changed=True,
    )


from ansible.module_utils.basic import *  # noqa


if __name__ == '__main__':
    main()
