#!/usr/bin/env python

import os
import re
import sys
import warnings
from bs4 import BeautifulSoup

# as based on dotenv

__version__ = '0.0.1'


line_re = re.compile(r"""
    ^
    (?:export\s+)?      # optional export
    ([\w\.]+)           # key
    (?:\s*=\s*|:\s+?)   # separator
    (                   # optional value begin
        '(?:\'|[^'])*'  #   single quoted value
        |               #   or
        "(?:\"|[^"])*"  #   double quoted value
        |               #   or
        [^#\n]+         #   unquoted value
    )?                  # value end
    (?:\s*\#.*)?        # optional comment
    $
""", re.VERBOSE)

variable_re = re.compile(r"""
    (\\)?               # is it escaped with a backslash?
    (\$)                # literal $
    (                   # collect braces with var for sub
        \{?             #   allow brace wrapping
        ([A-Z0-9_]+)    #   match the variable
        \}?             #   closing brace
    )                   # braces end
""", re.IGNORECASE | re.VERBOSE)


def read_dotenv(dotenv=None):
    """
    Read a .env file into os.environ.
    If not given a path to a dotenv path, does filthy magic stack backtracking
    to find manage.py and then find the dotenv.
    """
    if dotenv is None:
        frame_filename = sys._getframe().f_back.f_code.co_filename
        dotenv = os.path.join(os.path.dirname(frame_filename), '.env')

    if os.path.exists(dotenv):
        with open(dotenv) as f:
            return parse_dotenv(f.read())
    else:
        warnings.warn("Not reading {0} - it doesn't exist.".format(dotenv))


def parse_dotenv(content):
    env = {}

    for line in content.splitlines():
        m1 = line_re.search(line)

        if m1:
            key, value = m1.groups()

            if value is None:
                value = ''

            # Remove leading/trailing whitespace
            value = value.strip()

            # Remove surrounding quotes
            m2 = re.match(r'^([\'"])(.*)\1$', value)

            if m2:
                quotemark, value = m2.groups()
            else:
                quotemark = None

            # Unescape all chars except $ so variables can be escaped properly
            if quotemark == '"':
                value = re.sub(r'\\([^$])', '\1', value)

            if quotemark != "'":
                # Substitute variables in a value
                for parts in variable_re.findall(value):
                    if parts[0] == '\\':
                        # Variable is escaped, don't replace it
                        replace = ''.join(parts[1:-1])
                    else:
                        # Replace it with the value from the environment
                        replace = env.get(
                            parts[-1],
                            os.environ.get(parts[-1], '')
                        )

                    value = value.replace(''.join(parts[0:-1]), replace)

            env[key] = value

        elif not re.search(r'^\s*(?:#.*)?$', line):  # not comment or blank
            warnings.warn(
                "Line {0} doesn't match format".format(repr(line)),
                SyntaxWarning
            )

    return env


def get_text(xml=None):
    if not xml:
        xml = 'workspace.xml'
    f = open(xml)
    lines = f.read()
    f.close()
    return lines


def gen_xmls(env, xml_filename):
    # old_xml = get_text('/Users/ediliogallardo/projects/newage/github/id-provider/.idea/workspace.xml')
    old_xml = get_text(xml_filename)

    soup = BeautifulSoup(old_xml, "xml")
    disable_configs = ['GoApplicationRunConfiguration']

    for conf in soup.find_all('configuration'):
        conf_type = conf.get('type')
        if conf_type and (conf_type not in disable_configs):
            envs = conf.envs
            if envs:
                envs.clear()
            else:
                envs = soup.new_tag('envs')
                conf.append(envs)
            for n, v in env.iteritems():
                new_tag = soup.new_tag("env", value="{}".format(v))
                new_tag['name'] = n
                envs.append(new_tag)
            print conf
            print('='*80)
    new_xml = str(soup)
    return old_xml, new_xml


def save_file(backup_xml, xml):
    f = open(backup_xml, 'w+')
    f.write(xml)
    f.close()


def gen_default_envs():
    settings = raw_input("Enter settings filename: ")
    if '.' not in settings:
        settings += '.settings'
    d = {
        'GEVENT_SUPPORT': 0,
        'PYTHONUNBUFFERED': 1,
        'DJANGO_SETTINGS_MODULE': settings
    }
    return d


def update_dict_if_necessary(env, default):
    for k, v in default.iteritems():
        if k not in env:
            env[k] = v


def main():
    msg = 'Program only accept the folder where you want to run. Assumes that ./idea/ and .env are in the same folder'
    length = len(sys.argv)
    if length <= 2:
        if length == 1:
            folder = '.'
        else:
            folder = sys.argv[1]
        env_file = os.path.join(folder, '.env')
        env = read_dotenv(env_file)
        default_env = gen_default_envs()

        update_dict_if_necessary(env, default_env)

        xml_file = os.path.join(folder, '.idea/workspace.xml')
        old_xml, new_xml = gen_xmls(env, xml_file)
        print new_xml
        backup_xml = os.path.join(folder, '.idea/workspace_backup.xml')
        save_file(backup_xml, old_xml)
        save_file(xml_file, new_xml)
    else:
        warnings.warn(msg)

if __name__ == '__main__':
    main()
