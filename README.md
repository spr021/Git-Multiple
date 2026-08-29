# Git Multiple

Git Multiple is a small, safe, cross-platform command-line application for saving Git identities and switching `user.name` and `user.email`. It runs on Linux, macOS, and Windows, supports both global and repository-local configuration, and has no runtime Python dependencies.

> Git identity is separate from hosting authentication. This application changes the author attached to commits. SSH keys, HTTPS credentials, GitHub/GitLab login, and remote URLs remain managed by Git and your credential manager.

## Requirements

- Git available on `PATH` (`git --version` must work).
- Either a standalone Git Multiple executable from [GitHub Releases](https://github.com/spr021/Git-Multiple/releases), or Python 3.9+ for a source/portable installation.

## Install

### Standalone application (no Python required)

Download the file for your computer from [Releases](https://github.com/spr021/Git-Multiple/releases):

| Operating system | Release file |
| --- | --- |
| Linux x86-64 | `git-multiple-linux-x64` |
| macOS Intel | `git-multiple-macos-x64` |
| macOS Apple Silicon | `git-multiple-macos-arm64` |
| Windows x86-64 | `git-multiple-windows-x64.exe` |

Linux:

```sh
mkdir -p "$HOME/.local/bin"
install -m 755 git-multiple-linux-x64 "$HOME/.local/bin/git-multiple"
git-multiple doctor
```

Make sure `$HOME/.local/bin` is on `PATH`.

macOS (replace the filename with the Intel build when appropriate):

```sh
mkdir -p "$HOME/.local/bin"
install -m 755 git-multiple-macos-arm64 "$HOME/.local/bin/git-multiple"
git-multiple doctor
```

The automated release builds are not Apple-notarized. If Gatekeeper quarantines a binary that you downloaded from this repository's official release, either use the source installation below or explicitly approve it in **System Settings → Privacy & Security**.

Windows PowerShell:

```powershell
$InstallDir = "$env:LOCALAPPDATA\Programs\GitMultiple"
New-Item -ItemType Directory -Force $InstallDir | Out-Null
Move-Item .\git-multiple-windows-x64.exe "$InstallDir\git-multiple.exe"
[Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path", "User") + ";$InstallDir", "User")
```

Open a new terminal and run `git-multiple doctor`.

Verify any downloaded application before running it:

```sh
sha256sum -c SHA256SUMS.txt
```

On Windows, use `Get-FileHash .\git-multiple-windows-x64.exe -Algorithm SHA256` and compare it with `SHA256SUMS.txt`.

### Install from source

Clone the repository, then run the installer for your system:

```sh
git clone https://github.com/spr021/Git-Multiple.git
cd Git-Multiple
./install.sh                 # Linux or macOS
```

```powershell
git clone https://github.com/spr021/Git-Multiple.git
Set-Location Git-Multiple
.\install.ps1               # Windows PowerShell
```

The source installer uses `pip install --user`, does not require `sudo`, and does not modify a shell startup file. If the executable is not found, add Python's user scripts directory to `PATH`.

For an isolated install, [pipx](https://pipx.pypa.io/) users can instead run `pipx install .` from the checkout.

### Portable Python application

`git-multiple.pyz` from Releases works on all three operating systems with Python 3.9+:

```sh
python3 git-multiple.pyz --version   # Linux/macOS
py -3 git-multiple.pyz --version    # Windows
```

## Use

Add profiles:

```sh
git-multiple add --id personal --name "Alex Smith" --email alex@example.com
git-multiple add --id work --name "Alex Smith" --email alex@company.example
```

List profiles. The active global identity is marked with `*`:

```sh
git-multiple list
```

Switch the global Git identity from any directory:

```sh
git-multiple use personal
```

Apply an identity only to the repository in the current directory:

```sh
cd path/to/repository
git-multiple use work --scope local
```

Other useful commands:

```sh
git-multiple                 # interactive numbered selector
git-multiple current
git-multiple current --scope local
git-multiple remove work
git-multiple config-path
git-multiple doctor
git-multiple --help
```

The old flags `-a`, `-l`, and `-v` remain available. The original `./switch.sh` also forwards to the new application for shell users.

## Migrate from version 1

The old `config.env` file can be imported without executing it as shell code:

```sh
git-multiple import-legacy /path/to/config.env
```

Duplicate email addresses are skipped, so the import is safe to repeat. After checking `git-multiple list`, keep the old file somewhere private or remove it because it contains personal email addresses.

## Configuration locations

Profiles are saved atomically in the normal per-user application-data directory:

- Linux: `$XDG_CONFIG_HOME/git-multiple/profiles.json`, or `~/.config/git-multiple/profiles.json`
- macOS: `~/Library/Application Support/git-multiple/profiles.json`
- Windows: `%APPDATA%\git-multiple\profiles.json`

Set `GIT_MULTIPLE_CONFIG` to override this path, which is especially useful for automation and tests.

## Development and testing

The test suite uses only the Python standard library. Its end-to-end test isolates both the profile file and global Git configuration, so it never changes the developer's real Git identity.

```sh
python3 -m unittest discover -v
python3 scripts/build_zipapp.py
python3 dist/git-multiple.pyz --version
```

CI runs the full suite with Python 3.9 and 3.13 on Linux, macOS, and Windows. Tagged releases (`v2.0.0`, for example) additionally build and smoke-test each native executable on its target operating system, publish a portable `.pyz`, create SHA-256 checksums, and attach everything to a GitHub Release.

To publish a release after CI is green:

```sh
git tag v2.0.0
git push origin v2.0.0
```

## License

[MIT](LICENSE)
