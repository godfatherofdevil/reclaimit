#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
build_root="${BUILD_ROOT:-"$repo_root/build/debian"}"
package_root="$build_root/reclaimit-0.1.0"

if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
	echo "dpkg-buildpackage is required to build the Debian package." >&2
	echo "Install Debian packaging tools, then rerun this script." >&2
	echo "The package rules create /opt/reclaimit/venv with python -m venv and pip." >&2
	exit 1
fi

rm -rf "$package_root"
mkdir -p "$package_root"
tar -C "$repo_root" \
	--exclude '.git' \
	--exclude '.idea' \
	--exclude '.agents' \
	--exclude 'build' \
	-cf - . | tar -C "$package_root" -xf -
cp -a "$package_root/packaging/debian" "$package_root/debian"

cd "$package_root"
dpkg-buildpackage -us -uc -b
