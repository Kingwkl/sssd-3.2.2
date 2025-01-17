# SSSD is running as root user by default.
# Set --with sssd_user or bcond_without to run SSSD as non-root user(sssd).
%bcond_with sssd_user

%global rhel6_minor %(%{__grep} -o "6\\.[0-9]*" /etc/redhat-release |%{__sed} -s 's/6.//')
%global rhel7_minor %(%{__grep} -o "7\\.[0-9]*" /etc/redhat-release |%{__sed} -s 's/7.//')

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2: %global __python2 /usr/bin/python2}
%{!?python2_sitelib: %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%{!?python_provide: %global need_python_provide 1}
%if 0%{?need_python_provide}
%define python_provide() %{lua:
        function string.starts(String, Start)
                return string.sub(String, 1, string.len(Start)) == Start
        end
        package = rpm.expand("%{?1:%{1}}");
        vr = rpm.expand("%{?epoch:%{epoch}:}%{version}-%{release}")
        if (string.starts(package, "python2-")) then
                if (rpm.expand("%{?buildarch}") ~= "noarch") then
                        str = "Provides: python-" ..
                              string.sub(package, 9, string.len(package)) ..
                              "%{?_isa} = " .. vr;
                        print(rpm.expand(str));
                end
                print("\\nProvides: python-");
                print(string.sub(package, 9, string.len(package)));
                print(" = ");
                print(vr);
                --Obsoleting the previous default python package
                if (rpm.expand("%{?buildarch}") ~= "noarch") then
                        str = "\\nObsoletes: python-" ..
                              string.sub(package, 9, string.len(package)) ..
                              "%{?_isa} < " .. vr;
                        print(rpm.expand(str));
                end
                print("\\nObsoletes: python-");
                print(string.sub(package, 9, string.len(package)));
                print(" < ");
                print(vr);
        elseif (string.starts(package, "python3-")) then
                --No unversioned provides as python3 is not default
        else
                print("%python_provide: ERROR: ");
                print(package);
                print(" not recognized.");
        end
}
%endif

# Fedora and RHEL 6+
# we don't want to provide private python extension libs
%define __provides_exclude_from %{python2_sitearch}/.*\.so$
%define __provides_exclude_from %{python3_sitearch}/.*\.so$

# workaround for rpm 4.13
%define _empty_manifest_terminate_build 0

%if (0%{?fedora} || 0%{?rhel} >= 7)
    %global use_systemd 1
%endif

# on Fedora and RHEL7 p11_child needs a polkit config snippet to be allowed to
# talk to pcscd if SSSD runs as unprivileged user
%if (%{with sssd_user} && (0%{?fedora} || 0%{?rhel} >= 7))
    %global install_pcscd_polkit_rule 1
%else
    %global enable_polkit_rules_option --disable-polkit-rules-path
%endif

%if (0%{?use_systemd} == 1)
    %global with_initscript --with-initscript=systemd --with-systemdunitdir=%{_unitdir}
    %global with_syslog --with-syslog=journald
%else
    %global with_initscript --with-initscript=sysv
%endif

%if (0%{?fedora} > 28 || 0%{?rhel} > 7)
    %global use_openssl 1
%endif

%global enable_experimental 1

%if (0%{?enable_experimental} == 1)
    %global experimental --enable-all-experimental-features
%endif

# Determine the location of the LDB modules directory
%global ldb_modulesdir %(pkg-config --variable=modulesdir ldb)

%if (0%{?fedora} || 0%{?rhel} >= 7)
%define _hardened_build 1
%endif

%if (0%{?fedora} || 0%{?rhel} >= 7)
    %global with_cifs_utils_plugin 1
%else
    %global with_cifs_utils_plugin_option --disable-cifs-idmap-plugin
%endif

%if (0%{?fedora} || 0%{?rhel} > 7)
    %global with_python3 1
%else
    %global with_python3_option --without-python3-bindings
%endif

%if (0%{?fedora} > 28 || 0%{?rhel} > 7)
    %global with_python2_option --without-python2-bindings
%else
    %global with_python2 1
%endif

%global enable_systemtap 1
%if (0%{?enable_systemtap} == 1)
    %global enable_systemtap_opt --enable-systemtap
%endif

%global with_secrets 0
%global with_secret_responder --without-secrets

%if (0%{?fedora} >= 23 || 0%{?rhel} >= 7)
    %global with_kcm 1
    %global with_kcm_option --with-kcm
%else
    %global with_kcm_option --without-kcm
%endif

%if (0%{?fedora} >= 27 || 0%{?rhel} >= 7)
    %global with_gdm_pam_extensions 1
%else
    %global with_gdm_pam_extensions 0
%endif

# Do not try to detect the idmap version on RHEL6 to avoid conflicts between
# samba and samba4 package
%if (0%{?fedora} || 0%{?rhel} >= 7)
    %global detect_idmap_version 1
%else
    %global with_idmap_version --with-smb-idmap-interface-version=5
%endif

%global with_local_provider 0
%if (0%{?fedora} <= 28 || 0%{?rhel <= 7})
    %global with_local_provider 1
    %global enable_local_provider --enable-local-provider
%endif

Name: sssd
Version: 2.2.3
Release: 0%{?dist}
Group: Applications/System
Summary: System Security Services Daemon
License: GPLv3+
URL: https://pagure.io/SSSD/sssd/
Source0: %{name}-%{version}.tar.gz
BuildRoot: %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

### Patches ###

### Dependencies ###

Requires: sssd-common = %{version}-%{release}
Requires: sssd-ldap = %{version}-%{release}
Requires: sssd-krb5 = %{version}-%{release}
Requires: sssd-ipa = %{version}-%{release}
Requires: sssd-ad = %{version}-%{release}
Requires: sssd-proxy = %{version}-%{release}
%if (0%{?with_python3} == 1)
Requires: python3-sssdconfig = %{version}-%{release}
%else
Requires: python2-sssdconfig = %{version}-%{release}
%endif

%global servicename sssd
%global sssdstatedir %{_localstatedir}/lib/sss
%global dbpath %{sssdstatedir}/db
%global keytabdir %{sssdstatedir}/keytabs
%global pipepath %{sssdstatedir}/pipes
%global mcpath %{sssdstatedir}/mc
%global pubconfpath %{sssdstatedir}/pubconf
%global gpocachepath %{sssdstatedir}/gpo_cache
%global secdbpath %{sssdstatedir}/secrets
%global deskprofilepath %{sssdstatedir}/deskprofile

### Build Dependencies ###

BuildRequires: make
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
BuildRequires: m4
BuildRequires: gcc
BuildRequires: popt-devel
BuildRequires: libtalloc-devel
BuildRequires: libtevent-devel
BuildRequires: libtdb-devel
BuildRequires: libldb-devel
BuildRequires: libdhash-devel >= 0.4.2
BuildRequires: libcollection-devel
BuildRequires: libini_config-devel >= 1.1
BuildRequires: dbus-devel
BuildRequires: dbus-libs
BuildRequires: openldap-devel
BuildRequires: pam-devel
%if (0%{?use_openssl} == 1)
BuildRequires: p11-kit-devel
BuildRequires: openssl-devel
%endif
BuildRequires: nss-devel
BuildRequires: nspr-devel
BuildRequires: pcre-devel
BuildRequires: libxslt
BuildRequires: libxml2
BuildRequires: docbook-style-xsl
BuildRequires: krb5-devel
BuildRequires: c-ares-devel
%if (0%{?with_python2} == 1)
BuildRequires: python2-devel
%endif
%if (0%{?with_python3} == 1)
BuildRequires: python3-devel
%endif
BuildRequires: check-devel
BuildRequires: doxygen
BuildRequires: libselinux-devel
BuildRequires: libsemanage-devel
BuildRequires: bind-utils
BuildRequires: keyutils-libs-devel
BuildRequires: gettext-devel
BuildRequires: pkgconfig
BuildRequires: findutils
BuildRequires: glib2-devel
BuildRequires: selinux-policy-targeted
%if (0%{?fedora} || 0%{?epel})
BuildRequires: libcmocka-devel >= 1.0.0
BuildRequires: uid_wrapper
BuildRequires: nss_wrapper
BuildRequires: pam_wrapper

# Test CA requires openssl independent if SSSD is build with NSS or openssl,
# openssh is needed for ssh-keygen and NSS builds need nss-tools for certutil.
# Currently only cmocka based tests use the test CA. If it is used elsewhere
# you might want to move the following requires out of the if-block.
# If SSSD is build with OpenSSL instead of NSS p11tool from the gnutls-utils
# package and softhsm2-util from the softhsm package are needed to prepare the
# data needed for the p11_child Smartcard tests. Since p11_child only looks at
# slots with are flagged as 'removable' softhsm version 2.1.0 or higher is
# needed.
%if (0%{?use_openssl} == 1)
BuildRequires: gnutls-utils
BuildRequires: softhsm >= 2.1.0
%endif

BuildRequires: openssl
BuildRequires: openssh
BuildRequires: nss-tools
%endif
BuildRequires: libnl3-devel
%if (0%{?use_systemd} == 1)
BuildRequires: systemd-devel
BuildRequires: systemd
%endif
%if (0%{?with_cifs_utils_plugin} == 1)
BuildRequires: cifs-utils-devel
%endif
%if (0%{?fedora} || (0%{?rhel} >= 7))
BuildRequires: libnfsidmap-devel
%else
BuildRequires: nfs-utils-lib-devel
%endif

BuildRequires: samba4-devel
BuildRequires: libsmbclient-devel
%if (0%{?detect_idmap_version} == 1)
BuildRequires: samba-winbind
%endif

%if (0%{?enable_systemtap} == 1)
BuildRequires: systemtap-sdt-devel
%endif
%if (0%{?with_secrets} == 1)
BuildRequires: http-parser-devel
BuildRequires: libcurl-devel
%endif
%if (0%{?with_kcm} == 1)
BuildRequires: libuuid-devel
%endif
%if (0%{?with_secrets} == 1 || 0%{?with_kcm} == 1)
BuildRequires: jansson-devel
%endif
%if (0%{?with_gdm_pam_extensions} == 1)
BuildRequires: gdm-pam-extensions-devel
%endif

%description
Provides a set of daemons to manage access to remote directories and
authentication mechanisms. It provides an NSS and PAM interface toward
the system and a pluggable backend system to connect to multiple different
account sources. It is also the basis to provide client auditing and policy
services for projects like FreeIPA.

The sssd subpackage is a meta-package that contains the daemon as well as all
the existing back ends.

%package common
Summary: Common files for the SSSD
Group: Applications/System
License: GPLv3+
Requires: sssd-client%{?_isa} = %{version}-%{release}
Requires: libsss_sudo = %{version}-%{release}
Requires: libsss_autofs%{?_isa} = %{version}-%{release}
Requires: libsss_idmap = %{version}-%{release}
Conflicts: sssd < %{version}-%{release}
%if (0%{?use_systemd} == 1)
%{?systemd_requires}
%else
Requires(post): initscripts chkconfig
Requires(preun):  initscripts chkconfig
Requires(postun): initscripts chkconfig
%endif

### Provides ###
Provides: libsss_sudo-devel = %{version}-%{release}
Obsoletes: libsss_sudo-devel <= 1.9.93

%description common
Common files for the SSSD. The common package includes all the files needed
to run a particular back end, however, the back ends are packaged in separate
subpackages such as sssd-ldap.

%package client
Summary: SSSD Client libraries for NSS and PAM
Group: Applications/System
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description client
Provides the libraries needed by the PAM and NSS stacks to connect to the SSSD
service.

%package -n libsss_sudo
Summary: A library to allow communication between SUDO and SSSD
Group: Development/Libraries
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libsss_sudo
A utility library to allow communication between SUDO and SSSD

%package -n libsss_autofs
Summary: A library to allow communication between Autofs and SSSD
Group: Development/Libraries
License: LGPLv3+

%description -n libsss_autofs
A utility library to allow communication between Autofs and SSSD

%package tools
Summary: Userspace tools for use with the SSSD
Group: Applications/System
License: GPLv3+
Requires: sssd-common = %{version}-%{release}
# required by sss_obfuscate
%if (0%{?with_python3} == 1)
Requires: python3-sss = %{version}-%{release}
Requires: python3-sssdconfig = %{version}-%{release}
%else
Requires: python2-sss = %{version}-%{release}
Requires: python2-sssdconfig = %{version}-%{release}
%endif
%if (0%{?use_systemd} == 0)
Requires: /sbin/service
%endif

%description tools
Provides userspace tools for manipulating users, groups, and nested groups in
SSSD when using id_provider = local in /etc/sssd/sssd.conf.

Also provides several other administrative tools:
    * sss_debuglevel to change the debug level on the fly
    * sss_seed which pre-creates a user entry for use in kickstarts
    * sss_obfuscate for generating an obfuscated LDAP password
    * sssctl -- an sssd status and control utility

%if (0%{?with_python2} == 1)
%package -n python2-sssdconfig
Summary: SSSD and IPA configuration file manipulation classes and functions
Group: Applications/System
License: GPLv3+
BuildArch: noarch
%{?python_provide:%python_provide python2-sssdconfig}

%description -n python2-sssdconfig
Provides python2 files for manipulation SSSD and IPA configuration files.
%endif

%if (0%{?with_python3} == 1)
%package -n python3-sssdconfig
Summary: SSSD and IPA configuration file manipulation classes and functions
Group: Applications/System
License: GPLv3+
BuildArch: noarch
%{?python_provide:%python_provide python3-sssdconfig}

%description -n python3-sssdconfig
Provides python3 files for manipulation SSSD and IPA configuration files.
%endif

%if (0%{?with_python2} == 1)
%package -n python2-sss
Summary: Python2 bindings for sssd
Group: Development/Libraries
License: LGPLv3+
Requires: sssd-common = %{version}-%{release}
%{?python_provide:%python_provide python2-sss}

%description -n python2-sss
Provides python2 module for manipulating users, groups, and nested groups in
SSSD when using id_provider = local in /etc/sssd/sssd.conf.

Also provides several other useful python2 bindings:
    * function for retrieving list of groups user belongs to.
    * class for obfuscation of passwords
%endif

%if (0%{?with_python3} == 1)
%package -n python3-sss
Summary: Python3 bindings for sssd
Group: Development/Libraries
License: LGPLv3+
Requires: sssd-common = %{version}-%{release}
%{?python_provide:%python_provide python3-sss}

%description -n python3-sss
Provides python3 module for manipulating users, groups, and nested groups in
SSSD when using id_provider = local in /etc/sssd/sssd.conf.

Also provides several other useful python3 bindings:
    * function for retrieving list of groups user belongs to.
    * class for obfuscation of passwords
%endif

%if (0%{?with_python2} == 1)
%package -n python2-sss-murmur
Summary: Python2 bindings for murmur hash function
Group: Development/Libraries
License: LGPLv3+
%{?python_provide:%python_provide python2-sss-murmur}

%description -n python2-sss-murmur
Provides python2 module for calculating the murmur hash version 3
%endif

%if (0%{?with_python3} == 1)
%package -n python3-sss-murmur
Summary: Python3 bindings for murmur hash function
Group: Development/Libraries
License: LGPLv3+
%{?python_provide:%python_provide python3-sss-murmur}

%description -n python3-sss-murmur
Provides python3 module for calculating the murmur hash version 3
%endif

%package ldap
Summary: The LDAP back end of the SSSD
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: sssd-common = %{version}-%{release}
Requires: sssd-krb5-common = %{version}-%{release}

%description ldap
Provides the LDAP back end that the SSSD can utilize to fetch identity data
from and authenticate against an LDAP server.

%package krb5-common
Summary: SSSD helpers needed for Kerberos and GSSAPI authentication
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: cyrus-sasl-gssapi
Requires: sssd-common = %{version}-%{release}

%description krb5-common
Provides helper processes that the LDAP and Kerberos back ends can use for
Kerberos user or host authentication.

%package krb5
Summary: The Kerberos authentication back end for the SSSD
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: sssd-common = %{version}-%{release}
Requires: sssd-krb5-common = %{version}-%{release}

%description krb5
Provides the Kerberos back end that the SSSD can utilize authenticate
against a Kerberos server.

%package common-pac
Summary: Common files needed for supporting PAC processing
Group: Applications/System
License: GPLv3+
Requires: sssd-common = %{version}-%{release}

%description common-pac
Provides common files needed by SSSD providers such as IPA and Active Directory
for handling Kerberos PACs.

%package ipa
Summary: The IPA back end of the SSSD
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: sssd-common = %{version}-%{release}
Requires: sssd-krb5-common = %{version}-%{release}
Requires: libipa_hbac = %{version}-%{release}
Requires: bind-utils
Requires: sssd-common-pac = %{version}-%{release}

%description ipa
Provides the IPA back end that the SSSD can utilize to fetch identity data
from and authenticate against an IPA server.

%package ad
Summary: The AD back end of the SSSD
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: sssd-common = %{version}-%{release}
Requires: sssd-krb5-common = %{version}-%{release}
Requires: sssd-common-pac = %{version}-%{release}
Requires: bind-utils

%description ad
Provides the Active Directory back end that the SSSD can utilize to fetch
identity data from and authenticate against an Active Directory server.

%package proxy
Summary: The proxy back end of the SSSD
Group: Applications/System
License: GPLv3+
Conflicts: sssd < %{version}-%{release}
Requires: sssd-common = %{version}-%{release}

%description proxy
Provides the proxy back end which can be used to wrap an existing NSS and/or
PAM modules to leverage SSSD caching.

%package -n libsss_idmap
Summary: FreeIPA Idmap library
Group: Development/Libraries
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libsss_idmap
Utility library to convert SIDs to UNIX UIDs and GIDs

%package -n libsss_idmap-devel
Summary: FreeIPA Idmap library
Group: Development/Libraries
License: LGPLv3+
Requires: libsss_idmap = %{version}-%{release}

%description -n libsss_idmap-devel
Utility library to SIDs to UNIX UIDs and GIDs

%package -n libipa_hbac
Summary: FreeIPA HBAC Evaluator library
Group: Development/Libraries
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libipa_hbac
Utility library to validate FreeIPA HBAC rules for authorization requests

%package -n libipa_hbac-devel
Summary: FreeIPA HBAC Evaluator library
Group: Development/Libraries
License: LGPLv3+
Requires: libipa_hbac = %{version}-%{release}

%description -n libipa_hbac-devel
Utility library to validate FreeIPA HBAC rules for authorization requests

%if (0%{?with_python2} == 1)
%package -n python2-libipa_hbac
Summary: Python2 bindings for the FreeIPA HBAC Evaluator library
Group: Development/Libraries
License: LGPLv3+
Requires: libipa_hbac = %{version}-%{release}
Provides: libipa_hbac-python = %{version}-%{release}
Obsoletes: libipa_hbac-python < 1.12.90
%{?python_provide:%python_provide python2-libipa_hbac}

%description -n python2-libipa_hbac
The python2-libipa_hbac contains the bindings so that libipa_hbac can be
used by Python applications.
%endif

%if (0%{?with_python3} == 1)
%package -n python3-libipa_hbac
Summary: Python3 bindings for the FreeIPA HBAC Evaluator library
Group: Development/Libraries
License: LGPLv3+
Requires: libipa_hbac = %{version}-%{release}
%{?python_provide:%python_provide python3-libipa_hbac}

%description -n python3-libipa_hbac
The python3-libipa_hbac contains the bindings so that libipa_hbac can be
used by Python applications.
%endif

%package -n libsss_nss_idmap
Summary: Library for SID and certificate based lookups
Group: Development/Libraries
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libsss_nss_idmap
Utility library for SID and certificate based lookups

%package -n libsss_nss_idmap-devel
Summary: Library for SID and certificate based lookups
Group: Development/Libraries
License: LGPLv3+
Requires: libsss_nss_idmap = %{version}-%{release}

%description -n libsss_nss_idmap-devel
Utility library for SID and certificate based lookups

%if (0%{?with_python2} == 1)
%package -n python2-libsss_nss_idmap
Summary: Python2 bindings for libsss_nss_idmap
Group: Development/Libraries
License: LGPLv3+
Requires: libsss_nss_idmap = %{version}-%{release}
Provides: libsss_nss_idmap-python = %{version}-%{release}
Obsoletes: libsss_nss_idmap-python < 1.12.90
%{?python_provide:%python_provide python2-libsss_nss_idmap}

%description -n python2-libsss_nss_idmap
The python2-libsss_nss_idmap contains the bindings so that libsss_nss_idmap can
be used by Python applications.
%endif

%if (0%{?with_python3} == 1)
%package -n python3-libsss_nss_idmap
Summary: Python3 bindings for libsss_nss_idmap
Group: Development/Libraries
License: LGPLv3+
Requires: libsss_nss_idmap = %{version}-%{release}
%{?python_provide:%python_provide python3-libsss_nss_idmap}

%description -n python3-libsss_nss_idmap
The python3-libsss_nss_idmap contains the bindings so that libsss_nss_idmap can
be used by Python applications.
%endif

%package dbus
Summary: The D-Bus responder of the SSSD
Group: Applications/System
License: GPLv3+
Requires: sssd-common = %{version}-%{release}
%{?systemd_requires}

%description dbus
Provides the D-Bus responder of the SSSD, called the InfoPipe, that allows
the information from the SSSD to be transmitted over the system bus.

%if (0%{?install_pcscd_polkit_rule} == 1)
%package polkit-rules
Summary: Rules for polkit integration for SSSD
Group: Applications/System
License: GPLv3+
Requires: polkit >= 0.106
Requires: sssd-common = %{version}-%{release}

%description polkit-rules
Provides rules for polkit integration with SSSD. This is required
for smartcard support.
%endif

%package -n libsss_simpleifp
Summary: The SSSD D-Bus responder helper library
Group: Development/Libraries
License: GPLv3+
Requires: sssd-dbus = %{version}-%{release}
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libsss_simpleifp
Provides library that simplifies D-Bus API for the SSSD InfoPipe responder.

%package -n libsss_simpleifp-devel
Summary: The SSSD D-Bus responder helper library
Group: Development/Libraries
License: GPLv3+
Requires: dbus-devel
Requires: libsss_simpleifp = %{version}-%{release}

%description -n libsss_simpleifp-devel
Provides library that simplifies D-Bus API for the SSSD InfoPipe responder.

%package libwbclient
Summary: The SSSD libwbclient implementation
Group: Applications/System
License: GPLv3+ and LGPLv3+

%description libwbclient
The SSSD libwbclient implementation.

%package libwbclient-devel
Summary: Development libraries for the SSSD libwbclient implementation
Group:  Development/Libraries
License: GPLv3+ and LGPLv3+

%description libwbclient-devel
Development libraries for the SSSD libwbclient implementation.

%package winbind-idmap
Summary: SSSD's idmap_sss Backend for Winbind
Group:  Applications/System
License: GPLv3+ and LGPLv3+

%description winbind-idmap
The idmap_sss module provides a way for Winbind to call SSSD to map UIDs/GIDs
and SIDs.

%package nfs-idmap
Summary: SSSD plug-in for NFSv4 rpc.idmapd
Group:  Applications/System
License: GPLv3+

%description nfs-idmap
The libnfsidmap sssd module provides a way for rpc.idmapd to call SSSD to map
UIDs/GIDs to names and vice versa. It can be also used for mapping principal
(user) name to IDs(UID or GID) or to obtain groups which user are member of.

%package -n libsss_certmap
Summary: SSSD Certificate Mapping Library
Group: Development/Libraries
License: LGPLv3+
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig

%description -n libsss_certmap
Library to map certificates to users based on rules

%package -n libsss_certmap-devel
Summary: SSSD Certificate Mapping Library
Group: Development/Libraries
License: LGPLv3+
Requires: libsss_certmap = %{version}-%{release}

%description -n libsss_certmap-devel
Library to map certificates to users based on rules

%if (0%{?with_kcm} == 1)
%package kcm
Summary: An implementation of a Kerberos KCM server
Group:  Applications/System
License: GPLv3+
Requires: sssd-common = %{version}-%{release}
%{?systemd_requires}

%description kcm
An implementation of a Kerberos KCM server. Use this package if you want to
use the KCM: Kerberos credentials cache.
%endif

%prep
%setup -q -n %{name}-%{version}

%build
autoreconf -ivf

%configure \
    --with-test-dir=/dev/shm \
    --with-db-path=%{dbpath} \
    --with-mcache-path=%{mcpath} \
    --with-pipe-path=%{pipepath} \
    --with-pubconf-path=%{pubconfpath} \
    --with-gpo-cache-path=%{gpocachepath} \
    --with-init-dir=%{_initrddir} \
    --with-krb5-rcache-dir=%{_localstatedir}/cache/krb5rcache \
    --enable-nsslibdir=/%{_lib} \
    --enable-pammoddir=/%{_lib}/security \
    --enable-nfsidmaplibdir=%{_libdir}/libnfsidmap \
    --disable-static \
%if (0%{?use_openssl} == 1)
    --with-crypto=libcrypto \
%endif
    --disable-rpath \
%if %{with sssd_user}
    --with-sssd-user=sssd \
%endif
    %{with_initscript} \
    %{?with_syslog} \
    %{?with_cifs_utils_plugin_option} \
    %{?with_python2_option} \
    %{?with_python3_option} \
    %{?enable_polkit_rules_option} \
    %{?enable_systemtap_opt} \
    %{?with_secret_responder} \
    %{?with_kcm_option} \
    %{?with_idmap_version} \
    %{?enable_local_provider} \
    %{?experimental}

make %{?_smp_mflags} all

make %{?_smp_mflags} docs

%check
export CK_TIMEOUT_MULTIPLIER=10
make %{?_smp_mflags} check VERBOSE=yes
unset CK_TIMEOUT_MULTIPLIER

%install

%if (0%{?with_python3} == 1)
sed -i -e 's:/usr/bin/python:/usr/bin/python3:' src/tools/sss_obfuscate
%endif

make install DESTDIR=$RPM_BUILD_ROOT

# Prepare language files
/usr/lib/rpm/find-lang.sh $RPM_BUILD_ROOT sssd

# Copy default logrotate file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/logrotate.d
install -m644 src/examples/logrotate $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/sssd

# Make sure SSSD is able to run on read-only root
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rwtab.d
install -m644 src/examples/rwtab $RPM_BUILD_ROOT%{_sysconfdir}/rwtab.d/sssd

%if (0%{?with_cifs_utils_plugin} == 1)
# Create directory for cifs-idmap alternative
# Otherwise this directory could not be owned by sssd-client
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/cifs-utils
%endif

# Remove .la files created by libtool
find $RPM_BUILD_ROOT -name "*.la" -exec rm -f {} \;

# Suppress developer-only documentation
rm -Rf ${RPM_BUILD_ROOT}/%{_docdir}/%{name}

# Older versions of rpmbuild can only handle one -f option
# So we need to append to the sssd*.lang file
%if (0%{?with_python2} == 1)
for file in `ls $RPM_BUILD_ROOT/%{python2_sitelib}/*.egg-info 2> /dev/null`
do
    echo %{python2_sitelib}/`basename $file` >> python2_sssdconfig.lang
done
%endif

%if (0%{?with_python3} == 1)
for file in `ls $RPM_BUILD_ROOT/%{python3_sitelib}/*.egg-info 2> /dev/null`
do
    echo %{python3_sitelib}/`basename $file` >> python3_sssdconfig.lang
done
%endif

touch sssd.lang
for subpackage in sssd_ldap sssd_krb5 sssd_ipa sssd_ad sssd_proxy sssd_tools \
                  sssd_client sssd_dbus sssd_nfs_idmap sssd_winbind_idmap \
                  libsss_certmap sssd_kcm
do
    touch $subpackage.lang
done

for man in `find $RPM_BUILD_ROOT/%{_mandir}/??/man?/ -type f | sed -e "s#$RPM_BUILD_ROOT/%{_mandir}/##"`
do
    lang=`echo $man | cut -c 1-2`
    case `basename $man` in
        sss_cache*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd.lang
            ;;
        sss_ssh*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd.lang
            ;;
        sss_rpcidmapd*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_nfs_idmap.lang
            ;;
        sss_*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_tools.lang
            ;;
        sssctl*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_tools.lang
            ;;
        sssd_krb5_*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_client.lang
            ;;
        pam_sss*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_client.lang
            ;;
        sssd-ldap*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_ldap.lang
            ;;
        sssd-krb5*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_krb5.lang
            ;;
        sssd-ipa*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_ipa.lang
            ;;
        sssd-ad*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_ad.lang
            ;;
        sssd-proxy*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_proxy.lang
            ;;
        sssd-ifp*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_dbus.lang
            ;;
        sssd-kcm*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_kcm.lang
            ;;
        idmap_sss*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd_winbind_idmap.lang
            ;;
        sss-certmap*)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> libsss_certmap.lang
            ;;
        *)
            echo \%lang\(${lang}\) \%{_mandir}/${man}\* >> sssd.lang
            ;;
    esac
done

# Print these to the rpmbuild log
echo "sssd.lang:"
cat sssd.lang

%if (0%{?with_python2} == 1)
echo "python2_sssdconfig.lang:"
cat python2_sssdconfig.lang
%endif

%if (0%{?with_python3} == 1)
echo "python3_sssdconfig.lang:"
cat python3_sssdconfig.lang
%endif

for subpackage in sssd_ldap sssd_krb5 sssd_ipa sssd_ad sssd_proxy sssd_tools \
                  sssd_client sssd_dbus sssd_nfs_idmap sssd_winbind_idmap \
                  libsss_certmap sssd_kcm
do
    echo "$subpackage.lang:"
    cat $subpackage.lang
done

# must be defined after last occurrence of package otherwise
# RPM will overwrite %%license as soon as it parses a License: tag
%if 0%{?rhel} <= 6
%define license %doc
%endif

%files
%defattr(-,root,root,-)
%license COPYING

%files common -f sssd.lang
%defattr(-,root,root,-)
%license COPYING
%doc src/examples/sssd-example.conf
%{_sbindir}/sssd
%if (0%{?use_systemd} == 1)
%{_unitdir}/sssd.service
%{_unitdir}/sssd-autofs.socket
%{_unitdir}/sssd-autofs.service
%{_unitdir}/sssd-nss.socket
%{_unitdir}/sssd-nss.service
%{_unitdir}/sssd-pac.socket
%{_unitdir}/sssd-pac.service
%{_unitdir}/sssd-pam.socket
%{_unitdir}/sssd-pam-priv.socket
%{_unitdir}/sssd-pam.service
%{_unitdir}/sssd-ssh.socket
%{_unitdir}/sssd-ssh.service
%{_unitdir}/sssd-sudo.socket
%{_unitdir}/sssd-sudo.service
%else
%{_initrddir}/%{name}
%endif

%dir %{_libexecdir}/%{servicename}
%{_libexecdir}/%{servicename}/sssd_be
%{_libexecdir}/%{servicename}/sssd_nss
%{_libexecdir}/%{servicename}/sssd_pam
%{_libexecdir}/%{servicename}/sssd_autofs
%{_libexecdir}/%{servicename}/sssd_ssh
%{_libexecdir}/%{servicename}/sssd_sudo
%{_libexecdir}/%{servicename}/p11_child
%if (0%{?use_systemd} == 1)
%{_libexecdir}/%{servicename}/sssd_check_socket_activated_responders
%endif

%dir %{_libdir}/%{name}
# The files provider is intentionally packaged in -common
%{_libdir}/%{name}/libsss_files.so
%{_libdir}/%{name}/libsss_simple.so

#Internal shared libraries
%{_libdir}/%{name}/libsss_child.so
%{_libdir}/%{name}/libsss_crypt.so
%{_libdir}/%{name}/libsss_cert.so
%{_libdir}/%{name}/libsss_debug.so
%{_libdir}/%{name}/libsss_krb5_common.so
%{_libdir}/%{name}/libsss_ldap_common.so
%{_libdir}/%{name}/libsss_util.so
%{_libdir}/%{name}/libsss_semanage.so
%{_libdir}/%{name}/libsss_sbus.so
%{_libdir}/%{name}/libsss_sbus_sync.so
%{_libdir}/%{name}/libsss_iface.so
%{_libdir}/%{name}/libsss_iface_sync.so
%{_libdir}/%{name}/libifp_iface.so
%{_libdir}/%{name}/libifp_iface_sync.so
%if (0%{?with_secrets} == 1 || 0%{?with_kcm} == 1)
%{_libdir}/%{name}/libsss_secrets.so
%endif

%{ldb_modulesdir}/memberof.so
%{_bindir}/sss_ssh_authorizedkeys
%{_bindir}/sss_ssh_knownhostsproxy
%{_sbindir}/sss_cache
%{_libexecdir}/%{servicename}/sss_signal

%dir %{sssdstatedir}
%dir %{_localstatedir}/cache/krb5rcache
%attr(700,sssd,sssd) %dir %{dbpath}
%attr(775,sssd,sssd) %dir %{mcpath}
%attr(751,sssd,sssd) %dir %{deskprofilepath}
%ghost %attr(0664,sssd,sssd) %verify(not md5 size mtime) %{mcpath}/passwd
%ghost %attr(0664,sssd,sssd) %verify(not md5 size mtime) %{mcpath}/group
%ghost %attr(0664,sssd,sssd) %verify(not md5 size mtime) %{mcpath}/initgroups
%attr(755,sssd,sssd) %dir %{pipepath}
%attr(750,sssd,root) %dir %{pipepath}/private
%attr(755,sssd,sssd) %dir %{pubconfpath}
%attr(755,sssd,sssd) %dir %{gpocachepath}
%attr(750,sssd,sssd) %dir %{_var}/log/%{name}
%attr(711,sssd,sssd) %dir %{_sysconfdir}/sssd
%attr(711,sssd,sssd) %dir %{_sysconfdir}/sssd/conf.d
%if (0%{?use_openssl} == 1)
%attr(711,sssd,sssd) %dir %{_sysconfdir}/sssd/pki
%endif
%ghost %attr(0600,sssd,sssd) %config(noreplace) %{_sysconfdir}/sssd/sssd.conf
%dir %{_sysconfdir}/logrotate.d
%config(noreplace) %{_sysconfdir}/logrotate.d/sssd
%dir %{_sysconfdir}/rwtab.d
%config(noreplace) %{_sysconfdir}/rwtab.d/sssd
%dir %{_datadir}/sssd
%{_sysconfdir}/pam.d/sssd-shadowutils
%dir %{_libdir}/%{name}/conf
%{_libdir}/%{name}/conf/sssd.conf

%{_datadir}/sssd/cfg_rules.ini
%{_datadir}/sssd/sssd.api.conf
%{_datadir}/sssd/sssd.api.d
%{_mandir}/man1/sss_ssh_authorizedkeys.1*
%{_mandir}/man1/sss_ssh_knownhostsproxy.1*
%{_mandir}/man5/sssd.conf.5*
%{_mandir}/man5/sssd-files.5*
%{_mandir}/man5/sssd-simple.5*
%{_mandir}/man5/sssd-sudo.5*
%{_mandir}/man5/sssd-session-recording.5*
%{_mandir}/man8/sssd.8*
%{_mandir}/man8/sss_cache.8*
%if (0%{?enable_systemtap} == 1)
%dir %{_datadir}/sssd/systemtap
%{_datadir}/sssd/systemtap/id_perf.stp
%{_datadir}/sssd/systemtap/nested_group_perf.stp
%{_datadir}/sssd/systemtap/dp_request.stp
%{_datadir}/sssd/systemtap/ldap_perf.stp
%dir %{_datadir}/systemtap
%dir %{_datadir}/systemtap/tapset
%{_datadir}/systemtap/tapset/sssd.stp
%{_datadir}/systemtap/tapset/sssd_functions.stp
%{_mandir}/man5/sssd-systemtap.5*
%endif

%if (0%{?install_pcscd_polkit_rule} == 1)
%files polkit-rules
%{_datadir}/polkit-1/rules.d/*
%endif

%files ldap -f sssd_ldap.lang
%defattr(-,root,root,-)
%license COPYING
%{_libdir}/%{name}/libsss_ldap.so
%{_mandir}/man5/sssd-ldap.5*
%{_mandir}/man5/sssd-ldap-attributes.5*

%files krb5-common
%defattr(-,root,root,-)
%license COPYING
%attr(755,sssd,sssd) %dir %{pubconfpath}/krb5.include.d
%attr(4750,root,sssd) %{_libexecdir}/%{servicename}/ldap_child
%attr(4750,root,sssd) %{_libexecdir}/%{servicename}/krb5_child

%files krb5 -f sssd_krb5.lang
%defattr(-,root,root,-)
%license COPYING
%{_libdir}/%{name}/libsss_krb5.so
%{_mandir}/man5/sssd-krb5.5*

%files common-pac
%defattr(-,root,root,-)
%license COPYING
%{_libexecdir}/%{servicename}/sssd_pac

%files ipa -f sssd_ipa.lang
%defattr(-,root,root,-)
%license COPYING
%attr(700,sssd,sssd) %dir %{keytabdir}
%{_libdir}/%{name}/libsss_ipa.so
%attr(4750,root,sssd) %{_libexecdir}/%{servicename}/selinux_child
%{_mandir}/man5/sssd-ipa.5*

%files ad -f sssd_ad.lang
%defattr(-,root,root,-)
%license COPYING
%{_libdir}/%{name}/libsss_ad.so
%{_libexecdir}/%{servicename}/gpo_child
%{_mandir}/man5/sssd-ad.5*

%files proxy
%defattr(-,root,root,-)
%license COPYING
%attr(4750,root,sssd) %{_libexecdir}/%{servicename}/proxy_child
%{_libdir}/%{name}/libsss_proxy.so

%files dbus -f sssd_dbus.lang
%defattr(-,root,root,-)
%license COPYING
%{_libexecdir}/%{servicename}/sssd_ifp
%{_mandir}/man5/sssd-ifp.5*
%if (0%{?use_systemd} == 1)
%{_unitdir}/sssd-ifp.service
%endif
# InfoPipe DBus plumbing
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.sssd.infopipe.conf
%{_datadir}/dbus-1/system-services/org.freedesktop.sssd.infopipe.service

%files -n libsss_simpleifp
%defattr(-,root,root,-)
%{_libdir}/libsss_simpleifp.so.*

%files -n libsss_simpleifp-devel
%defattr(-,root,root,-)
%doc sss_simpleifp_doc/html
%{_includedir}/sss_sifp.h
%{_includedir}/sss_sifp_dbus.h
%{_libdir}/libsss_simpleifp.so
%{_libdir}/pkgconfig/sss_simpleifp.pc

%files client -f sssd_client.lang
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
/%{_lib}/libnss_sss.so.2
/%{_lib}/security/pam_sss.so
%{_libdir}/krb5/plugins/libkrb5/sssd_krb5_locator_plugin.so
%{_libdir}/krb5/plugins/authdata/sssd_pac_plugin.so
%if (0%{?with_cifs_utils_plugin} == 1)
%dir %{_libdir}/cifs-utils
%{_libdir}/cifs-utils/cifs_idmap_sss.so
%dir %{_sysconfdir}/cifs-utils
%ghost %{_sysconfdir}/cifs-utils/idmap-plugin
%endif
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/modules
%{_libdir}/%{name}/modules/sssd_krb5_localauth_plugin.so
%{_mandir}/man8/pam_sss.8*
%{_mandir}/man8/sssd_krb5_locator_plugin.8*

%files -n libsss_sudo
%defattr(-,root,root,-)
%license src/sss_client/COPYING
%{_libdir}/libsss_sudo.so*

%files -n libsss_autofs
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
%dir %{_libdir}/%{name}/modules
%{_libdir}/%{name}/modules/libsss_autofs.so

%files tools -f sssd_tools.lang
%defattr(-,root,root,-)
%license COPYING
%if (0%{with_local_provider} == 1)
%{_sbindir}/sss_useradd
%{_sbindir}/sss_userdel
%{_sbindir}/sss_usermod
%{_sbindir}/sss_groupadd
%{_sbindir}/sss_groupdel
%{_sbindir}/sss_groupmod
%{_sbindir}/sss_groupshow
%endif
%{_sbindir}/sss_obfuscate
%{_sbindir}/sss_override
%{_sbindir}/sss_debuglevel
%{_sbindir}/sss_seed
%{_sbindir}/sssctl
%if (0%{with_local_provider} == 1)
%{_mandir}/man8/sss_groupadd.8*
%{_mandir}/man8/sss_groupdel.8*
%{_mandir}/man8/sss_groupmod.8*
%{_mandir}/man8/sss_groupshow.8*
%{_mandir}/man8/sss_useradd.8*
%{_mandir}/man8/sss_userdel.8*
%{_mandir}/man8/sss_usermod.8*
%endif
%{_mandir}/man8/sss_obfuscate.8*
%{_mandir}/man8/sss_override.8*
%{_mandir}/man8/sss_debuglevel.8*
%{_mandir}/man8/sss_seed.8*
%{_mandir}/man8/sssctl.8*

%if (0%{?with_python2} == 1)
%files -n python2-sssdconfig -f python2_sssdconfig.lang
%defattr(-,root,root,-)
%dir %{python2_sitelib}/SSSDConfig
%{python2_sitelib}/SSSDConfig/*.py*
%endif

%if (0%{?with_python3} == 1)
%files -n python3-sssdconfig -f python3_sssdconfig.lang
%defattr(-,root,root,-)
%dir %{python3_sitelib}/SSSDConfig
%{python3_sitelib}/SSSDConfig/*.py*
%dir %{python3_sitelib}/SSSDConfig/__pycache__
%{python3_sitelib}/SSSDConfig/__pycache__/*.py*
%endif

%if (0%{?with_python2} == 1)
%files -n python2-sss
%defattr(-,root,root,-)
%{python2_sitearch}/pysss.so
%endif

%if (0%{?with_python3} == 1)
%files -n python3-sss
%defattr(-,root,root,-)
%{python3_sitearch}/pysss.so
%endif

%if (0%{?with_python2} == 1)
%files -n python2-sss-murmur
%defattr(-,root,root,-)
%{python2_sitearch}/pysss_murmur.so
%endif

%if (0%{?with_python3} == 1)
%files -n python3-sss-murmur
%defattr(-,root,root,-)
%{python3_sitearch}/pysss_murmur.so
%endif

%files -n libsss_idmap
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
%{_libdir}/libsss_idmap.so.*

%files -n libsss_idmap-devel
%defattr(-,root,root,-)
%doc idmap_doc/html
%{_includedir}/sss_idmap.h
%{_libdir}/libsss_idmap.so
%{_libdir}/pkgconfig/sss_idmap.pc

%files -n libipa_hbac
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
%{_libdir}/libipa_hbac.so.*

%files -n libipa_hbac-devel
%defattr(-,root,root,-)
%doc hbac_doc/html
%{_includedir}/ipa_hbac.h
%{_libdir}/libipa_hbac.so
%{_libdir}/pkgconfig/ipa_hbac.pc

%files -n libsss_nss_idmap
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
%{_libdir}/libsss_nss_idmap.so.*

%files -n libsss_nss_idmap-devel
%defattr(-,root,root,-)
%doc nss_idmap_doc/html
%{_includedir}/sss_nss_idmap.h
%{_libdir}/libsss_nss_idmap.so
%{_libdir}/pkgconfig/sss_nss_idmap.pc

%if (0%{?with_python2} == 1)
%files -n python2-libsss_nss_idmap
%defattr(-,root,root,-)
%{python2_sitearch}/pysss_nss_idmap.so
%endif

%if (0%{?with_python3} == 1)
%files -n python3-libsss_nss_idmap
%defattr(-,root,root,-)
%{python3_sitearch}/pysss_nss_idmap.so
%endif

%if (0%{?with_python2} == 1)
%files -n python2-libipa_hbac
%defattr(-,root,root,-)
%{python2_sitearch}/pyhbac.so
%endif

%if (0%{?with_python3} == 1)
%files -n python3-libipa_hbac
%defattr(-,root,root,-)
%{python3_sitearch}/pyhbac.so
%endif

%files libwbclient
%defattr(-,root,root,-)
%dir %{_libdir}/%{name}
%dir %{_libdir}/%{name}/modules
%{_libdir}/%{name}/modules/libwbclient.so.*

%files libwbclient-devel
%defattr(-,root,root,-)
%{_includedir}/wbclient_sssd.h
%{_libdir}/%{name}/modules/libwbclient.so
%{_libdir}/pkgconfig/wbclient_sssd.pc

%files winbind-idmap -f sssd_winbind_idmap.lang
%dir %{_libdir}/samba/idmap
%{_libdir}/samba/idmap/sss.so
%{_mandir}/man8/idmap_sss.8*

%files nfs-idmap -f sssd_nfs_idmap.lang
%{_mandir}/man5/sss_rpcidmapd.5*
%{_libdir}/libnfsidmap/sss.so

%files -n libsss_certmap -f libsss_certmap.lang
%defattr(-,root,root,-)
%license src/sss_client/COPYING src/sss_client/COPYING.LESSER
%{_libdir}/libsss_certmap.so.*
%{_mandir}/man5/sss-certmap.5*

%files -n libsss_certmap-devel
%defattr(-,root,root,-)
%doc certmap_doc/html
%{_includedir}/sss_certmap.h
%{_libdir}/libsss_certmap.so
%{_libdir}/pkgconfig/sss_certmap.pc

%if (0%{?with_kcm} == 1)
%files kcm -f sssd_kcm.lang
%attr(700,root,root) %dir %{secdbpath}
%{_libexecdir}/%{servicename}/sssd_kcm
%if (0%{?with_secrets} == 1)
%{_libexecdir}/%{servicename}/sssd_secrets
%endif
%dir %{_datadir}/sssd-kcm
%{_datadir}/sssd-kcm/kcm_default_ccache
%{_unitdir}/sssd-kcm.socket
%{_unitdir}/sssd-kcm.service
%{_mandir}/man8/sssd-kcm.8*
%if (0%{?with_secrets} == 1)
%{_unitdir}/sssd-secrets.socket
%{_unitdir}/sssd-secrets.service
%{_mandir}/man5/sssd-secrets.5*
%endif
%endif

%pre common
getent group sssd >/dev/null || groupadd -r sssd
getent passwd sssd >/dev/null || useradd -r -g sssd -d / -s /sbin/nologin -c "User for sssd" sssd

%if (0%{?use_systemd} == 1)
# systemd
%post common
%systemd_post sssd.service
%systemd_post sssd-autofs.socket
%systemd_post sssd-nss.socket
%systemd_post sssd-pac.socket
%systemd_post sssd-pam.socket
%systemd_post sssd-pam-priv.socket
%systemd_post sssd-ssh.socket
%systemd_post sssd-sudo.socket

%preun common
%systemd_preun sssd.service
%systemd_preun sssd-autofs.socket
%systemd_preun sssd-nss.socket
%systemd_preun sssd-pac.socket
%systemd_preun sssd-pam.socket
%systemd_preun sssd-pam-priv.socket
%systemd_preun sssd-ssh.socket
%systemd_preun sssd-sudo.socket

%postun common
%systemd_postun_with_restart sssd.service
%systemd_postun_with_restart sssd-autofs.socket
%systemd_postun_with_restart sssd-autofs.service
%systemd_postun_with_restart sssd-nss.socket
%systemd_postun_with_restart sssd-nss.service
%systemd_postun_with_restart sssd-pac.socket
%systemd_postun_with_restart sssd-pac.service
%systemd_postun_with_restart sssd-pam.socket
%systemd_postun_with_restart sssd-pam-priv.socket
%systemd_postun_with_restart sssd-pam.service
%systemd_postun_with_restart sssd-ssh.socket
%systemd_postun_with_restart sssd-ssh.service
%systemd_postun_with_restart sssd-sudo.socket
%systemd_postun_with_restart sssd-sudo.service

%post dbus
%systemd_post sssd-ifp.service

%preun dbus
%systemd_preun sssd-ifp.service

%postun dbus
%systemd_postun_with_restart sssd-ifp.service

%if (0%{?with_kcm} == 1)
%post kcm
%systemd_post sssd-kcm.socket

%preun kcm
%systemd_preun sssd-kcm.socket

%postun kcm
%systemd_postun_with_restart sssd-kcm.socket
%systemd_postun_with_restart sssd-kcm.service
%endif

%if (0%{?with_secrets} == 1)
%post secrets
%systemd_postun_with_restart sssd-secrets.socket

%preun secrets
%systemd_preun_with_restart sssd-secrets.socket

%postun secrets
%systemd_postun_with_restart sssd-secrets.socket
%systemd_postun_with_restart sssd-secrets.service
%endif

%else
# sysv
%post common
/sbin/chkconfig --add %{servicename}

%posttrans
/sbin/service %{servicename} condrestart 2>&1 > /dev/null

%preun common
if [ $1 = 0 ] ; then
    /sbin/service %{servicename} stop 2>&1 > /dev/null
    /sbin/chkconfig --del %{servicename}
fi
%endif

%if (0%{?with_cifs_utils_plugin} == 1)
%post client
/sbin/ldconfig
/usr/sbin/alternatives --install /etc/cifs-utils/idmap-plugin cifs-idmap-plugin %{_libdir}/cifs-utils/cifs_idmap_sss.so 20

%preun client
if [ $1 -eq 0 ] ; then
        /usr/sbin/alternatives --remove cifs-idmap-plugin %{_libdir}/cifs-utils/cifs_idmap_sss.so
fi
%else
%post client -p /sbin/ldconfig
%endif

%postun client -p /sbin/ldconfig

%post -n libsss_sudo -p /sbin/ldconfig

%postun -n libsss_sudo -p /sbin/ldconfig

%post -n libipa_hbac -p /sbin/ldconfig

%postun -n libipa_hbac -p /sbin/ldconfig

%post -n libsss_idmap -p /sbin/ldconfig

%postun -n libsss_idmap -p /sbin/ldconfig

%post -n libsss_nss_idmap -p /sbin/ldconfig

%postun -n libsss_nss_idmap -p /sbin/ldconfig

%post -n libsss_simpleifp -p /sbin/ldconfig

%postun -n libsss_simpleifp -p /sbin/ldconfig

%post -n libsss_certmap -p /sbin/ldconfig

%postun -n libsss_certmap -p /sbin/ldconfig

%changelog
* Mon Mar 15 2010 Stephen Gallagher <sgallagh@redhat.com> - 2.2.3-0
- Automated build of the SSSD
