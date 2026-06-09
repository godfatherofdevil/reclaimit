Name: reclaimit
Version: 0.1.0
Release: 1%{?dist}
Summary: TUI client for bidirectional iOS media sync
License: MIT
Source0: %{name}-%{version}.tar.gz
BuildArch: noarch

BuildRequires: python3 >= 3.12
BuildRequires: python3dist(pip)
BuildRequires: python3dist(wheel)
Requires: python3 >= 3.12
Requires: libimobiledevice
Requires: usbmuxd

%description
Reclaimit discovers, pairs, browses, plans, and transfers iOS media on
Linux and Unix-like systems using libimobiledevice-compatible services.

%prep
%setup -q

%build
python3 -m venv %{_builddir}/reclaimit-venv
%{_builddir}/reclaimit-venv/bin/python -m pip wheel --disable-pip-version-check --no-cache-dir --wheel-dir %{_builddir}/reclaimit-wheels .
%{_builddir}/reclaimit-venv/bin/python -m pip install --disable-pip-version-check --no-cache-dir --no-index --find-links %{_builddir}/reclaimit-wheels reclaimit

%install
mkdir -p %{buildroot}/opt/reclaimit
cp -a %{_builddir}/reclaimit-venv %{buildroot}/opt/reclaimit/venv
sed -i '1s|^#!.*|#!/opt/reclaimit/venv/bin/python|' %{buildroot}/opt/reclaimit/venv/bin/reclaimit
mkdir -p %{buildroot}%{_bindir}
install -m 0755 packaging/scripts/reclaimit-launcher %{buildroot}%{_bindir}/reclaimit

%files
%{_bindir}/reclaimit
/opt/reclaimit/venv
