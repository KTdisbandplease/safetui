Name:           safetui
Version:        3.5.0
Release:        1%{?dist}
Summary:        Menu-driven firewall, SELinux, lockout guard and backup tool

License:        MIT
URL:            https://github.com/KTdisbandplease/safetui
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

Requires:       dialog
Requires:       newt
Requires:       firewalld
Requires:       policycoreutils
Requires:       policycoreutils-python-utils
Requires:       libselinux-utils
# ausearch, used when building an allow policy from denial logs
Requires:       audit
# backup menu: cp/find/stat, gzip, tar, ionice/logger
Requires:       coreutils
Requires:       findutils
Requires:       gzip
Requires:       tar
Requires:       util-linux
# safetui-guard: nft, systemd-run, who/ps for terminal notices
Requires:       procps-ng
Requires:       nftables
Requires:       systemd

%description
safetui is a terminal menu (TUI) for server work on RHEL, Rocky Linux and
AlmaLinux 9. It lets you manage the firewall (firewalld) and SELinux, protects
risky remote changes with a lockout guard that rolls back automatically, and
takes backups, without having to remember the commands.

 - Firewall: view ports / services / source IPs, open and close ports,
   allow a port from one IP only, add and remove services
 - SELinux: status and mode, port policy, Booleans, file contexts,
   allow policy from denial logs (audit2allow), module removal
 - Lockout guard (safetui-guard): snapshot before a change and automatic
   rollback unless confirmed in time, even if the SSH session is lost
 - Backup: files and folders with owner / mode / SELinux label preserved,
   MariaDB dumps with retention, scheduled DB backup (systemd timer)

English and Korean user interface.

%prep
%setup -q

%build
# shell scripts only, nothing to build

%install
rm -rf %{buildroot}
install -D -m 0755 src/safetui       %{buildroot}%{_bindir}/safetui
install -D -m 0755 src/safetui-guard %{buildroot}%{_bindir}/safetui-guard
install -D -m 0644 src/dialogrc       %{buildroot}%{_datadir}/safetui/dialogrc
install -d -m 0700 %{buildroot}%{_sharedstatedir}/safetui-guard

%preun
# On erase (not upgrade) also remove the scheduled DB backup timer
if [ "$1" -eq 0 ]; then
    systemctl disable --now safetui-dbbackup.timer >/dev/null 2>&1 || :
    rm -f /etc/systemd/system/safetui-dbbackup.timer /etc/systemd/system/safetui-dbbackup.service
    systemctl daemon-reload >/dev/null 2>&1 || :
fi

%posttrans
# Re-register a saved backup schedule (for example after replacing another build)
%{_bindir}/safetui --apply-schedule >/dev/null 2>&1 || :

%files
%license LICENSE
%doc README.md
%{_bindir}/safetui
%{_bindir}/safetui-guard
%{_datadir}/safetui/dialogrc
%dir %attr(0700,root,root) %{_sharedstatedir}/safetui-guard

%changelog
* Fri Oct 23 2026 JJ <mrwhitehacker@naver.com> - 3.5.0-1
- Security hardening after an external review (findings S15-S24):
  - safetui-guard: __rollback / __warn now require root; do_rollback only
    restores from inside the snapshot root, so no caller can point it at an
    arbitrary directory; rollback only runs while a guard is armed; the timer
    binary is resolved like the backup schedule (installed copy, else a
    root-only path) instead of a hardcoded path
  - A database name can no longer start with a hyphen, and a user-supplied name
    is passed to mariadb-dump after "--" so it cannot act as an option
  - SELinux inputs are validated (port number, module name, absolute path) so
    they cannot be read as options by semanage / audit2allow / restorecon
  - The password file is removed on a wait timeout, the cron log is created
    owner-only, the settings folder is created 0700, and the crontab entry
    quotes its script path
  - preflight checks for whiptail; a normal user may back up folders they own;
    bk_tar_all detects a failing find via pipefail

* Thu Oct 22 2026 JJ <mrwhitehacker@naver.com> - 3.4.0-1
- A second screen style, chosen from the new "Screen" item in the main menu:
  the familiar dialog windows, or screens drawn by safetui itself that show a
  one-line description under every menu item. The accent colour is settable
  (orange, sky, green, purple, pink, yellow). Classic stays the default
- Menus, messages, confirmations, long output, the input box, the wait boxes
  and the checklists all follow the chosen style. Picking files to back up is
  still drawn by dialog
- The file browser is drawn in the chosen style too, so no screen falls back to
  dialog any more
- A normal user can only back up what they own. Being able to read a file was
  not enough of a reason: cp happily copies a world-readable system file, and
  the copy then belongs to whoever ran the backup. Such entries are listed and
  marked "not yours" but cannot be picked, folders stay walkable so people can
  still reach their own files, and the copy itself refuses them as well
- The schedule can no longer end up half applied. The settings are saved first
  and nothing is registered if that fails; the crontab line is only written once
  the script it calls exists, and is taken back out if any step fails. A
  schedule whose script went missing is rebuilt when the schedule screen opens
- The new screens redraw without clearing first and leave as one write, and no
  longer fork a process per row, so they stop flashing and keep up with the
  keyboard (a 22-row frame went from 73 ms to 3 ms). The file browser reads the
  folder only when the folder changes
- Fixed: writing the draw redirection as `exec 3>/dev/tty 2>/dev/null` also sent
  the script's own stderr to /dev/null for good, and dialog draws on stderr, so
  the classic screens would have shown nothing at all

* Thu Oct 22 2026 JJ <mrwhitehacker@naver.com> - 3.3.0-1
- Normal users can now run safetui without root. The menu then shows only what
  works without privileges: file / DB backup, the schedule and read-only status.
  Firewall and SELinux stay root-only - without root they answer "Authorization
  failed", and a menu that can only fail is worse than no menu
- A normal user keeps settings in ~/.config/safetui, backups in ~/safetui-backups
  (mode 700), and falls back to those when the packaged defaults point at a
  root-only folder
- The schedule can run from crontab as well as a systemd timer. Root may pick
  either; a normal user always gets crontab, because a per-user systemd timer
  stops at logout unless lingering is enabled. Switching method removes the other
  one, so the backup never runs twice
- Scheduled runs go through a generated script (db-backup.sh); "last day of the
  month" is handled there, since cron cannot express it

* Mon Oct 19 2026 JJ <mrwhitehacker@naver.com> - 3.2.3-1
- Scheduled DB backup: wait (up to 5 minutes) until the database answers before
  dumping. When the server was off at the scheduled time, the catch-up run
  right after boot started before MariaDB and failed with "Can't connect to
  local server through socket"
- The schedule unit is ordered after mariadb / mysqld when both start at boot;
  existing schedules are rewritten on upgrade

* Thu Oct 15 2026 JJ <mrwhitehacker@naver.com> - 3.2.2-1
- Backup failure screens show the hint line as well, so when a backup folder is
  refused (created by another account, or a symbolic link on the path) the fix
  is on screen instead of only the reason

* Thu Oct 15 2026 JJ <mrwhitehacker@naver.com> - 3.2.1-1
- Backups now default to /var/backups/safetui instead of /tmp
  (the OS deletes old files under /tmp, and on a tmpfs /tmp they are lost on reboot)
- Backup folders are created root-only (700); file names no longer reveal
  database names or the backup schedule to other accounts
- The scheduled backup unit runs the installed /usr/bin/safetui; another path is
  used only when it is root-owned and not writable by others
- Database names read from backup.conf are checked the same way as menu input,
  and are split without filename expansion

* Thu Oct 15 2026 JJ <mrwhitehacker@naver.com> - 3.2.0-1
- Firewall: add several ports at once, separated by commas
  (e.g. 3030,1234,10000-12000); nothing is added if one of them is invalid
- Firewall: remove several ports, source IPs or IP-specific rules at once
  (checklist instead of a single choice)
- Firewall: assign several source IPs at once, and create IP-specific rules
  for several IPs and ports in one go (every IP x every port)
- The window is redrawn in the middle when the terminal is resized while it
  is shown (dialog left it where it was, cut off at the edge)
- English screens no longer show Korean text in the language menu (it showed
  as boxes on the Linux console)

* Thu Oct 15 2026 JJ <mrwhitehacker@naver.com> - 3.1.2-1
- Lockout guard, network rollback: bring back only the connections that were
  active when the guard was armed, each on its own device. Before, every profile
  was activated, so an unused second profile of the same interface could take it
  over and leave the server on the wrong address
- Restart NetworkManager only when one of those connections does not come back,
  not whenever any unrelated device is disconnected
- Read nmcli output in English, so device states are recognised on servers
  running in another language
- Lockout guard without firewalld: the saved nftables ruleset now replaces the
  current one on rollback instead of being added on top of it (duplicate rules)
- safetui-guard arm: reject a missing option value (it used to loop forever),
  unknown targets (a typo armed a guard that protected nothing) and a timeout
  outside 30-86400 seconds
- Port input: only 1-65535, and a range must not be reversed
- Backup settings: a value ending in a single "=" (e.g. a generated DB password)
  lost that "=" when the settings were read back, so DB backups failed to log in

* Thu Oct 15 2026 JJ <mrwhitehacker@naver.com> - 3.1.1-1
- Fix: after switching the language in the menu, the lockout guard countdown
  at the top right kept showing the previous language until safetui was restarted

* Mon Oct 12 2026 JJ <mrwhitehacker@naver.com> - 3.1.0-1
- Lockout guard: a rollback now also brings services back. If firewalld, sshd or
  NetworkManager was running when the guard was armed and has been stopped,
  disabled or masked since, it is unmasked / enabled / started again
- The history file records which services were started again

* Wed Oct 07 2026 JJ <mrwhitehacker@naver.com> - 3.0.0-1
- The project is now called safetui. Commands are safetui and safetui-guard;
  settings live in /etc/safetui, logs in /var/log/safetui-*.log, and the
  systemd units are named safetui-guard and safetui-dbbackup

* Fri Oct 02 2026 JJ <mrwhitehacker@naver.com> - 2.12.0-1
- First public release
- English is the default language; Korean remains available from the menu
- Neutral defaults: MariaDB under /usr, backups under /tmp/backup
- Packagers can ship defaults in /usr/share/safetui/defaults.conf
- Refuse to write backups under a world-writable folder (such as /tmp) when a
  folder on the path was created by another account or is a symbolic link
- Add LICENSE (MIT)

* Fri Oct 02 2026 JJ <mrwhitehacker@naver.com> - 2.11.0-1
- ESC on the main menu moves the cursor to <Quit> instead of quitting
- About / Help split into About, Help and Commands
- Lockout guard: remaining time shown inside the screen, notice after a
  rollback, history in /var/log/safetui-guard.log
- Fix: Ctrl+C removed the temporary directory while the program kept running

* Thu Oct 01 2026 JJ <mrwhitehacker@naver.com> - 2.8.0-1
- Backup menu: files and folders, MariaDB dumps, retention, gzip option,
  tar bundling, scheduled DB backup (daily / weekly / monthly)

* Tue Sep 15 2026 JJ <mrwhitehacker@naver.com> - 2.5.0-1
- Firewall: allow a port from one IP only; warn before changes that can cut
  the SSH session
- SELinux: choose the program when building an allow policy, list only
  locally installed modules, Boolean picker
- Hardening: input validation, private temporary directory

* Mon Aug 31 2026 JJ <mrwhitehacker@naver.com> - 2.0.0-1
- Korean / English user interface
- Lockout guard (safetui-guard) with selectable targets

* Thu Aug 27 2026 JJ <mrwhitehacker@naver.com> - 1.0.0-1
- Initial version: firewall and SELinux menus
