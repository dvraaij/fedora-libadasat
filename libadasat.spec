# The test suite is normally run. It can be disabled with "--without=check".
%bcond_without check

# Upstream source information.
%global upstream_owner    AdaCore
%global upstream_name     AdaSAT
%global upstream_version  24.0.0
%global upstream_gittag   v%{upstream_version}

Name:           libadasat
Version:        %{upstream_version}
Release:        1%{?dist}
Summary:        An implementation of a DPLL-based SAT solver in Ada

License:        Apache-2.0 WITH LLVM-exception

URL:            https://github.com/%{upstream_owner}/%{upstream_name}
Source:         %{url}/archive/%{upstream_gittag}/%{upstream_name}-%{upstream_version}.tar.gz

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
%autosetup -n %{upstream_name}-%{upstream_version} -p1


###########
## Build ##
###########

%build

gprbuild %{GPRbuild_flags} -XVERSION=%{version} \
         -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
         -P adasat.gpr


#############
## Install ##
#############

%install

gprinstall %{GPRinstall_flags} -XVERSION=%{version} \
           -XBUILD_MODE=prod -XLIBRARY_TYPE=relocatable \
           -P adasat.gpr

# Fix up some things that GPRinstall does wrong.
ln --symbolic --force %{name}.so.%{version} %{buildroot}%{_libdir}/%{name}.so

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

# Create an override for directories.gpr.
mkdir testsuite/multilib
cat << EOF > ./testsuite/multilib/directories.gpr
abstract project Directories is
   Libdir     := "%{buildroot}%{_libdir}";
   Includedir := "%{buildroot}%{_includedir}";
end Directories;
EOF

# Make the files installed in the buildroot and the override for directories.gpr
# visible to the test runner.
export PATH=%{buildroot}%{_bindir}:$PATH
export LIBRARY_PATH=%{buildroot}%{_libdir}:$LIBRARY_PATH
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}:$LD_LIBRARY_PATH
export GPR_PROJECT_PATH=${PWD}/testsuite/multilib:%{buildroot}%{_GNAT_project_dir}:$GPR_PROJECT_PATH

# Run the tests.
%python3 testsuite/testsuite.py \
         --show-error-output \
         --max-consecutive-failures=4

%endif


###########
## Files ##
###########

%files
%license LICENSE
%doc README*
%{_libdir}/%{name}.so.%{version}


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
* Sat Aug 12 2023 Dennis van Raaij <dvraaij@fedoraproject.org> - 24.0.0-1
- New package.
