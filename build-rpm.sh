#!/usr/bin/env bash
#
# Build the secpanel RPM.
# Run on RHEL / Rocky / AlmaLinux 9 (or anywhere rpmbuild is available).
#
#   sudo dnf install -y rpm-build rpmdevtools
#   ./build-rpm.sh
#
# Result: ~/rpmbuild/RPMS/noarch/secpanel-<version>-1.*.noarch.rpm
#
set -euo pipefail

NAME=secpanel
VERSION=2.12.0
HERE="$(cd "$(dirname "$0")" && pwd)"

command -v rpmbuild >/dev/null 2>&1 || {
    echo "rpmbuild not found. Install it first:"
    echo "  sudo dnf install -y rpm-build rpmdevtools"
    exit 1
}

rpmdev-setuptree 2>/dev/null || mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Source tarball with the <name>-<version>/ top directory that %setup expects
STAGE="$(mktemp -d)"
DEST="$STAGE/${NAME}-${VERSION}"
mkdir -p "$DEST/src"
install -m 0755 "$HERE/src/secpanel"       "$DEST/src/secpanel"
install -m 0755 "$HERE/src/secpanel-guard" "$DEST/src/secpanel-guard"
install -m 0644 "$HERE/src/dialogrc"       "$DEST/src/dialogrc"
install -m 0644 "$HERE/README.md"          "$DEST/README.md"
install -m 0644 "$HERE/LICENSE"            "$DEST/LICENSE"

tar -C "$STAGE" -czf ~/rpmbuild/SOURCES/"${NAME}-${VERSION}".tar.gz "${NAME}-${VERSION}"
cp "$HERE/rpm/${NAME}.spec" ~/rpmbuild/SPECS/

rpmbuild -bb ~/rpmbuild/SPECS/"${NAME}.spec"

rm -rf "$STAGE"

echo
echo "Build finished. Install with:"
echo "  sudo dnf install ~/rpmbuild/RPMS/noarch/${NAME}-${VERSION}-1.*.noarch.rpm"
