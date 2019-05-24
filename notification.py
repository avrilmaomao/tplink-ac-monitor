#!/usr/bin/env python
import subprocess
import os


def show(title, content):
    os_uname = os.uname()[0]
    if os_uname == 'Darwin':
        show_on_osx(title, content)
    if os_uname == 'Linux':
        show_on_android(title, content)


def show_on_osx(title, content):
    command = '''osascript -e 'display notification "%s" with title "%s"' '''% (content, title)
    subprocess.call(command, shell=True)


def show_on_android(title, content):
    command = '''termux-notification --title "%s" --sound  --content "%s"''' % (title, content)
    subprocess.call(command, shell=True)


if __name__ == '__main__':
    show('ap 0001离线', '请检查')