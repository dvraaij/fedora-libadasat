# Temporary version for use in the library soname.  A temporary version with
# only 2 parts (e.g., 0.1), as recommended by the Fedora packaging guidelines,
# does not work.  GPRbuild seems truncate version "0.1" to just "0".
%global version_soname 0.0.1

# Run the test suite.
%bcond_without check

# Upstream source information.
%global upstream_owner  AdaCore
%global upstream_name   AdaSAT
%global upstream_commit f948e2271aec51f9313fa41ff3c00230a483f9e8

Name:           libadasat
Version:        0^20230120gitf948e22
Release:        1%{?dist}
Summary:        An implementation of a DPLL-based SAT solver in Ada

License:        Apache-2.0

URL:            https://github.com/%{upstream_owner}/%{upstream_name}
Source0:        %{url}/archive/%{upstream_commit}.tar.gz

# [Fedora-specific] Set library soname.
Patch:          %{name}-set-soname-of-adasat-library.patch

BuildRequires:  gcc-gnat gprbuild
# A fedora-gnat-project-common that contains GPRbuild_flags is needed.
BuildRequires:  fedora-gnat-project-common >= 3.17
%if %{with check}
BuildRequires:  python-devel
BuildRequires:  python-setuptools
BuildRequires:  python3-e3-testsuite
%endif

# Alternative name.
Provides:       adasat = %{version}

# Build only on architectures where GPRbuild is available.
ExclusiveArch:  %{GPRbuild_arches}

%global common_description_en \
Implementation of a DPLL-based SAT solver in Ada. Main features: conflict \
analysis and backjumping, two-watched literals scheme, at-Most-One constraints \
and custom theories.

%description %{common_description_en}


#################
## Subpackages ##
#################

%package devel
Summary:        Development files for AdaSAT
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       fedora-gnat-project-common

%description devel %{common_description_en}

This package contains source code and linking information for developing
applications that use AdaSAT.


#############
## Prepare ##
#############

%prep
%autosetup -n %{upstream_name}-%{upstream_commit}


###########
## Build ##
###########

%build

gprbuild %{GPRbuild_flags} -XVERSION=%{version_soname} \
         -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
         -P adasat.gpr


#############
## Install ##
#############

%install

gprinstall %{GPRinstall_flags} -XVERSION=%{version_soname} \
           -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
           -P adasat.gpr

# Fix up some things that GPRinstall does wrong.
ln --symbolic --force %{name}.so.%{version_soname} %{buildroot}%{_libdir}/%{name}.so

# Keep a copy of the unmodified GNAT project files when running the test suite.
%if %{with check}
%global GNAT_project_dir_orig %{_GNAT_project_dir}_orig
cp -r %{buildroot}%{_GNAT_project_dir} %{buildroot}%{GNAT_project_dir_orig}
%endif

# Make the generated usage project file architecture-independent.
sed --regexp-extended --in-place \
    '--expression=1i with "directories";' \
    '--expression=/^--  This project has been generated/d' \
    '--expression=/package Linker is/,/end Linker/d' \
    '--expression=s|^( *for +Source_Dirs +use +).*;$|\1(Directories.Includedir \& "/'%{name}'");|i' \
    '--expression=s|^( *for +Library_Dir +use +).*;$|\1Directories.Libdir;|i' \
    '--expression=s|^( *for +Library_ALI_Dir +use +).*;$|\1Directories.Libdir \& "/'%{name}'";|i' \
    %{buildroot}%{_GNAT_project_dir}/adasat.gpr
# The Sed commands are:
# 1: Insert a with clause before the first line to import the directories
#    project.
# 2: Delete a comment that mentions the architecture.
# 3: Delete the package Linker, which contains linker parameters that a
#    shared library normally doesn't need, and can contain architecture-
#    specific pathnames.
# 4: Replace the value of Source_Dirs with a pathname based on
#    Directories.Includedir.
# 5: Replace the value of Library_Dir with Directories.Libdir.
# 6: Replace the value of Library_ALI_Dir with a pathname based on
#    Directories.Libdir.


###########
## Check ##
###########

%if %{with check}
%check

# Make the files installed in the buildroot visible to the testsuite.
export PATH=%{buildroot}%{_bindir}:$PATH
export LIBRARY_PATH=%{buildroot}%{_libdir}:$LIBRARY_PATH
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}:$LD_LIBRARY_PATH
export GPR_PROJECT_PATH=%{buildroot}%{GNAT_project_dir_orig}:$GPR_PROJECT_PATH

# Run the tests.
%python3 testsuite/testsuite.py \
         --show-error-output \
         --max-consecutive-failures=4

# Remove the unmodified, non-multilib GNAT project files.
rm -r %{buildroot}%{GNAT_project_dir_orig}

%endif


###########
## Files ##
###########

%files
%license LICENSE
%doc README*
%{_libdir}/%{name}.so.%{version_soname}


%files devel
%{_GNAT_project_dir}/adasat.gpr
%{_includedir}/%{name}
%dir %{_libdir}/%{name}
%attr(444,-,-) %{_libdir}/%{name}/*.ali
%{_libdir}/%{name}.so


###############
## Changelog ##
###############

%changelog
* Sat Aug 12 2023 Dennis van Raaij <dvraaij@fedoraproject.org> - 0^20230120gitf948e22-1
- New package.
