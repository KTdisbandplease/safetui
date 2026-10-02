Name:           secpanel
Version:        2.12.0
Release:        1%{?dist}
Summary:        Menu-driven firewall, SELinux, lockout guard and backup tool

License:        MIT
URL:            https://github.com/KTdisbandplease/secpanel
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
# secpanel-guard: nft, systemd-run, who/ps for terminal notices
Requires:       procps-ng
Requires:       nftables
Requires:       systemd

%description
secpanel is a terminal menu (TUI) for server work on RHEL, Rocky Linux and
AlmaLinux 9. It lets you manage the firewall (firewalld) and SELinux, protects
risky remote changes with a lockout guard that rolls back automatically, and
takes backups, without having to remember the commands.

 - Firewall: view ports / services / source IPs, open and close ports,
   allow a port from one IP only, add and remove services
 - SELinux: status and mode, port policy, Booleans, file contexts,
   allow policy from denial logs (audit2allow), module removal
 - Lockout guard (secpanel-guard): snapshot before a change and automatic
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
install -D -m 0755 src/secpanel       %{buildroot}%{_bindir}/secpanel
install -D -m 0755 src/secpanel-guard %{buildroot}%{_bindir}/secpanel-guard
install -D -m 0644 src/dialogrc       %{buildroot}%{_datadir}/secpanel/dialogrc
install -d -m 0700 %{buildroot}%{_sharedstatedir}/secpanel-guard

%preun
# On erase (not upgrade) also remove the scheduled DB backup timer
if [ "$1" -eq 0 ]; then
    systemctl disable --now secpanel-dbbackup.timer >/dev/null 2>&1 || :
    rm -f /etc/systemd/system/secpanel-dbbackup.timer /etc/systemd/system/secpanel-dbbackup.service
    systemctl daemon-reload >/dev/null 2>&1 || :
fi

%posttrans
# Re-register a saved backup schedule (for example after replacing another build)
%{_bindir}/secpanel --apply-schedule >/dev/null 2>&1 || :

%files
%license LICENSE
%doc README.md
%{_bindir}/secpanel
%{_bindir}/secpanel-guard
%{_datadir}/secpanel/dialogrc
%dir %attr(0700,root,root) %{_sharedstatedir}/secpanel-guard

%changelog
* Fri Oct 02 2026 JJ <mrwhitehacker@naver.com> - 2.12.0-1
- First public release
- English is the default language; Korean remains available from the menu
- Neutral defaults: MariaDB under /usr, backups under /tmp/backup
- Packagers can ship defaults in /usr/share/secpanel/defaults.conf
- Refuse to write backups under a world-writable folder (such as /tmp) when a
  folder on the path was created by another account or is a symbolic link
- Add LICENSE (MIT)

* Fri Oct 02 2026 JJ <mrwhitehacker@naver.com> - 2.11.0-1
- ESC on the main menu moves the cursor to <Quit> instead of quitting
- About / Help split into About, Help and Commands
- Lockout guard: remaining time shown inside the screen, notice after a
  rollback, history in /var/log/secpanel-guard.log
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
- Lockout guard (secpanel-guard) with selectable targets

* Thu Aug 27 2026 JJ <mrwhitehacker@naver.com> - 1.0.0-1
- Initial version: firewall and SELinux menus
