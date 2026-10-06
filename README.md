# safetui

A terminal menu (TUI) for everyday server work on RHEL / Rocky Linux / AlmaLinux 9:
**firewall, SELinux, a lockout guard with automatic rollback, and backups** — all from
one screen, without having to remember the commands.

- Target: **RHEL / Rocky Linux / AlmaLinux 9**, run as root (`sudo safetui`)
- Languages: **English** (default) and **Korean** — switch from the main menu, or
  `safetui --english` / `safetui --korean`
- Pure shell scripts on top of `dialog` / `whiptail`. No daemon, no open port.

## Download

**[Download the latest RPM](https://github.com/KTdisbandplease/safetui/releases/latest/download/safetui-latest.el9.noarch.rpm)**
(RHEL / Rocky Linux / AlmaLinux 9, noarch) — or install it straight from the URL:

```bash
sudo dnf install -y https://github.com/KTdisbandplease/safetui/releases/latest/download/safetui-latest.el9.noarch.rpm
sudo safetui
```

All versions are on the [Releases](https://github.com/KTdisbandplease/safetui/releases) page.

## Features

### Firewall (firewalld)
- View open ports, services and allowed source IPs; whole policy at a glance
- Open / close ports, add / remove services
- **Allow a port from one IP only** (rich rule), shown as a plain sentence
- Warns before a change that could cut your own SSH session (removing the `ssh` service,
  the SSH port, or a source IP) and offers to arm the lockout guard first
- Every change is saved with `--permanent` and reloaded

### SELinux
- Status, switch Enforcing <-> Permissive
- Port policy, Boolean switches, file contexts (`semanage`, `setsebool -P`, `restorecon`)
- Build an allow policy from denial logs (`audit2allow`) — you pick the program first and
  see a preview, so unrelated denials are not allowed by accident
- Remove policy modules (only the ones you installed are listed)

### Lockout guard (`safetui-guard`)
A dead-man switch for risky remote changes.
- Snapshots firewall / sshd / network settings and schedules an automatic rollback
- If you do not confirm within the time limit, **systemd reverts the change — even if your
  SSH session is gone**
- Remaining time is shown at the top right of the safetui screen; other logged-in
  terminals get a one-line reminder every 10 seconds during the last minute
- After a rollback you are told so, and every arm / confirm / rollback is recorded in
  `/var/log/safetui-guard.log` (`safetui-guard log`)

### Backup
- **Files and folders**: pick them in a file browser (arrow keys, Space to select, Enter to
  open a folder). Owner, group, mode, timestamps and SELinux labels are preserved (`cp -a`).
  Symbolic links are skipped. Optionally bundle several items into one tar file.
- **MariaDB**: dump without stopping the service (`--single-transaction`, low CPU / IO
  priority), optional gzip, old dumps removed after a retention period
- **Scheduled DB backup**: daily / weekly / monthly (a day or the last day) at a set time.
  This is a systemd timer that runs `safetui --db-backup` once — safetui does not stay
  running in the background.
- History of file backups, list of DB dumps

## Build from source

Build the RPM yourself on RHEL / Rocky / AlmaLinux 9:

```bash
sudo dnf install -y rpm-build rpmdevtools
./build-rpm.sh
sudo dnf install ~/rpmbuild/RPMS/noarch/safetui-*.noarch.rpm
```

Or run it without packaging:

```bash
sudo install -m 0755 src/safetui /usr/bin/safetui
sudo install -m 0755 src/safetui-guard /usr/bin/safetui-guard
```

(Both must be in `/usr/bin`: the rollback timer and the backup schedule call them by that path.)

## Usage

```bash
sudo safetui
```

| Key | Action |
|---|---|
| Up / Down | move |
| Enter | select / run |
| Tab | move to the buttons |
| Space | check / uncheck in lists |
| ESC, Ctrl+C | back one level. On the main menu ESC only moves the cursor to `<Quit>` |
| Ctrl+L | redraw the screen |

Main menu 6 (**About / Help**) has three pages: *About*, *Help* (keys and tips) and
*Commands* (how to do the same things without the menu).

Command-line use:

```bash
safetui --version
sudo safetui --db-backup                 # run the configured DB backup once
sudo safetui-guard arm --timeout 300 --targets firewall --note "port change"
sudo safetui-guard ok                    # confirm, keep the change
sudo safetui-guard status                # also: rollback, log
```

## Backup settings

Stored in `/etc/safetui/backup.conf` (root only, mode 600). Change them from
**Backup > Backup settings**.

| Setting | Default | Notes |
|---|---|---|
| DB install path | `/usr` | `bin/mariadb-dump` under this path is used |
| DB user / password | `root` / none | the password is optional |
| Database name | all databases | several names separated by spaces |
| DB backup folder | `/tmp/backup/db` | **change this** — see below |
| DB backup retention | 30 days | 0 = keep forever |
| DB backup gzip | on | off saves plain `.sql` |
| File backup folder | same folder as the original | or one folder for everything (`/tmp/backup/files`) |
| Backup name suffix | `_$today` | `$today` = YYYYMMDD, `$time` = HHMMSS |
| If it already exists | ask | add a number / overwrite / skip |
| Bundle many into tar | off | |

**About the default `/tmp/backup` location.** It works out of the box, but `/tmp` is not a
place to keep backups: on RHEL 9 files in `/tmp` are deleted automatically after about
10 days, and they share a disk with everything else. Point the backup folders at a
dedicated location before relying on them. Because `/tmp` is writable by every user,
safetui refuses to write a backup under it if any folder on the path was created by
another account or is a symbolic link.

A packager can ship different defaults in `/usr/share/safetui/defaults.conf`
(same `KEY=value` format as `backup.conf`, plus `UI_LANG=en|ko`).

## Security notes

- Both commands require root; there is no setuid helper, no daemon and no listening port.
- User input is passed to commands as arguments, never through `eval`.
- The DB password is stored in a root-only file and handed to `mariadb-dump` through a
  temporary root-only options file, not on the command line.
- Dump files are created with mode 600; a backup folder created by safetui is mode 700.
- Temporary files live in a private directory created with `mktemp -d`.

## Dependencies

Installed automatically by the RPM. All are in the base repositories of RHEL 9 and its rebuilds.

`dialog newt firewalld policycoreutils policycoreutils-python-utils libselinux-utils audit
nftables systemd procps-ng coreutils findutils gzip tar util-linux`

MariaDB is not a dependency: the DB backup uses the client found under the configured path
and shows a warning if there is none.

## License and third-party software

safetui itself is released under the **MIT License** — see [LICENSE](LICENSE).

safetui does not include or link any third-party code. It runs the following system tools
as separate programs; each stays under its own license:

| Tool (package) | License | Used for |
|---|---|---|
| bash | GPL-3.0-or-later | the scripts run on it |
| dialog | LGPL-2.1 | menus, lists, text boxes |
| newt (whiptail) | LGPL-2.0 | input boxes |
| firewalld | GPL-2.0-or-later | firewall management |
| policycoreutils, policycoreutils-python-utils | GPL-2.0-or-later | `semanage`, `restorecon`, `semodule`, `audit2allow` |
| libselinux-utils | Public Domain | `getenforce`, `setenforce` |
| audit | GPL-2.0-or-later | `ausearch` |
| nftables | GPL-2.0 | ruleset snapshot for the guard |
| systemd | LGPL-2.1-or-later | rollback timer, scheduled backup |
| procps-ng | GPL-2.0-or-later / LGPL-2.0-or-later | `ps` |
| coreutils, findutils, tar | GPL-3.0-or-later | copying, searching, archiving |
| gzip | GPL-3.0-or-later | dump compression |
| util-linux | GPL-2.0-or-later and others | `ionice`, `logger` |
| MariaDB client (optional) | GPL-2.0 | `mariadb-dump` |
