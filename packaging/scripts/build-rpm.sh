#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
topdir="${RPM_TOPDIR:-"$repo_root/build/rpm"}"
name=reclaimit
version=0.1.0
source_dir="$topdir/SOURCES/$name-$version"
archive="$topdir/SOURCES/$name-$version.tar.gz"

if ! command -v rpmbuild >/dev/null 2>&1; then
	echo "rpmbuild is required to build the RPM package." >&2
	echo "Install RPM packaging tools, then rerun this script." >&2
	echo "The spec creates /opt/reclaimit/venv with python -m venv and pip." >&2
	exit 1
fi

rm -rf "$source_dir"
mkdir -p "$topdir/BUILD" "$topdir/BUILDROOT" "$topdir/RPMS" "$topdir/SOURCES" "$topdir/SPECS" "$topdir/SRPMS" "$source_dir"
tar -C "$repo_root" \
	--exclude '.git' \
	--exclude '.idea' \
	--exclude '.agents' \
	--exclude 'build' \
	-cf - . | tar -C "$source_dir" -xf -
tar -C "$topdir/SOURCES" -czf "$archive" "$name-$version"
cp "$repo_root/packaging/rpm/reclaimit.spec" "$topdir/SPECS/reclaimit.spec"

rpmbuild --define "_topdir $topdir" -ba "$topdir/SPECS/reclaimit.spec"
