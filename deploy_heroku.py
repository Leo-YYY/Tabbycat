#!/usr/bin/python

import argparse
import subprocess
import re

parser = argparse.ArgumentParser(description="Deploy Tabbycat to a new Heroku app.")
parser.add_argument("urlname", type=str, help="Name of the Heroku app. The app will be at urlname.herokuapp.com. Use '-' to use a Heroku-generated default.")
parser.add_argument("--public-cache-timeout", type=int, default=None, help="Set the public page cache timeout to TIMEOUT", metavar="TIMEOUT")
parser.add_argument("--tab-cache-timeout", type=int, default=None, help="Set the tab page cache timeout to TIMEOUT", metavar="TIMEOUT")
parser.add_argument("--enable-debug", action="store_true", default=False, help="Enable Django debug pages")
parser.add_argument("--no-open", action="store_false", default=True, dest="open", help="Don't open the Heroku website in your browser at the end")
parser.add_argument("--import-tournament", type=str, help="Also run the import_tournament command, importing from IMPORT_DIR", metavar="IMPORT_DIR")
parser.add_argument("--git-remote-name", type=str, help="Name of Git remote to use", default=None)
args = parser.parse_args()

def print_command(command):
    print "\033[1;36m $ " + " ".join(command) + "\033[0m"

def run_command(command):
    print_command(command)
    subprocess.check_call(command)

def run_heroku_command(command):
    command.insert(0, "heroku")
    command.extend(["--app", urlname])
    run_command(command)

def print_yellow(message):
    print "\033[1;32m" + message + "\033[0m"

# Create the app
command = ["heroku", "apps:create"]
if args.urlname != "-":
    command.append(args.urlname)
print_command(command)
output = subprocess.check_output(command)
print output
match = re.search("https://([\w_-]+)\.herokuapp\.com/\s+\|\s+(https://git.heroku.com/[\w_-]+.git)", output)
urlname = match.group(1)
heroku_url = match.group(2)

# Add add-ons
run_heroku_command(["addons:create", "memcachier"])

# Set config variables
command = ["config:add", "WAITRESS_THREADS=4"]
command.append("DEBUG=1" if args.enable_debug else "DEBUG=0")
if args.public_cache_timeout:
    command.append("PUBLIC_PAGE_CACHE_TIMEOUT=%d" % args.public_cache_timeout)
if args.tab_cache_timeout:
    command.append("TAB_PAGES_CACHE_TIMEOUT=%d" % args.tab_cache_timeout)
run_heroku_command(command)

# Set up a remote, if applicable
remote_name = args.git_remote_name or urlname
run_command(["git", "remote", "add", remote_name, heroku_url])

# Push source code to Heroku
run_command(["git", "push", remote_name, "master"])

run_heroku_command(["run", "python", "manage.py", "migrate", "auth"])
run_heroku_command(["run", "python", "manage.py", "migrate"])
run_heroku_command(["run", "python", "manage.py", "makemigrations", "debate"])
run_heroku_command(["run", "python", "manage.py", "migrate"])

print_yellow("Now creating a superuser for the Heroku site.")
print_yellow("You'll need to respond to the prompts:")
run_heroku_command(["run", "python", "manage.py", "createsuperuser"])

if args.import_tournament:
    run_heroku_command(["run", "python", "manage.py", "import_tournament", args.import_tournament])

if args.open:
    run_heroku_command(["open"])