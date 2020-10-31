#!/usr/bin/env python3
import os
import subprocess
from selfdrive.swaglog import cloudlog

cloak = True

def get_git_branch():
  try:
    return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf8').strip()
  except subprocess.CalledProcessError:
    return None


def get_git_commit(branch: str = "HEAD", default: Optional[str] = None) -> Optional[str]:
  if cloak:
    return "a3bef4c46274e16ca6d1b71c8ef5d02f942f7bd0"
  return run_cmd_default(["git", "rev-parse", branch], default=default)


def get_git_branch(default: Optional[str] = None) -> Optional[str]:
  if cloak:
    return "release2"
  return run_cmd_default(["git", "rev-parse", "--abbrev-ref", "HEAD"], default=default)


def get_git_full_branchname(default: Optional[str] = None) -> Optional[str]:
  if cloak:
    return "origin/release2"
  return run_cmd_default(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], default=default)


def get_git_remote(default: Optional[str] = None) -> Optional[str]:
  if cloak:
    return "https://github.com/commaai/openpilot.git"
  try:
    local_branch = subprocess.check_output(["git", "name-rev", "--name-only", "HEAD"], encoding='utf8').strip()
    tracking_remote = subprocess.check_output(["git", "config", "branch." + local_branch + ".remote"], encoding='utf8').strip()
    return subprocess.check_output(["git", "config", "remote." + tracking_remote + ".url"], encoding='utf8').strip()

  except subprocess.CalledProcessError:
    try:
      # Not on a branch, fallback
      return subprocess.check_output(["git", "config", "--get", "remote.origin.url"], encoding='utf8').strip()
    except subprocess.CalledProcessError:
      return None


with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "common", "version.h")) as _versionf:
  version = _versionf.read().split('"')[1]

training_version = b"0.2.0"
terms_version = b"2"

dirty = True
origin = get_git_remote()
branch = get_git_full_branchname()
try:
  try:
    subprocess.check_call(["git", "update-index", "--refresh"])
  except subprocess.CalledProcessError:
    pass
  # This is needed otherwise touched files might show up as modified
  try:
    if cloak:
      comma_remote = origin.startswith('git@github.com:commaai') or origin.startswith('https://github.com/commaai')
    else:
      comma_remote = origin.startswith('git@github.com:AskAlice') or origin.startswith('https://github.com/AskAlice')
    tested_branch = get_git_branch() in ['release2', 'release3', 'release4', 'release5', 'release6']

    dirty = not comma_remote
    if not cloak:
      dirty = dirty or (subprocess.call(["git", "diff-index", "--quiet", branch, "--"]) != 0)

    if dirty:
      dirty_files = subprocess.check_output(["git", "diff-index", branch, "--"], encoding='utf8')
      commit = subprocess.check_output(["git", "rev-parse", "--verify", "HEAD"], encoding='utf8').rstrip()
      origin_commit = subprocess.check_output(["git", "rev-parse", "--verify", branch], encoding='utf8').rstrip()
      cloudlog.event("dirty comma branch", version=version, dirty=dirty, origin=origin, branch=branch,
                           dirty_files=dirty_files, commit=commit, origin_commit=origin_commit)

  except subprocess.CalledProcessError:
    dirty = True
    cloudlog.exception("git subprocess failed while checking dirty")

except subprocess.CalledProcessError:
  dirty = True
  cloudlog.exception("git subprocess failed while checking dirty")


if __name__ == "__main__":
  print("Dirty: %s" % dirty)
  print("Version: %s" % version)
  print("Remote: %s" % origin)
  print("Branch %s" % branch)
