# Project-type signals

Map the markers found by `inventory.sh` (the `### MARKERS` section) to a project type.
Most real projects mix a few; pick the dominant type and note the rest. State a
confidence level and cite the evidence.

| Type | Strong signals |
|------|----------------|
| **Static website** | `index.html` + plain `.css`/`.js`, no framework manifest, no build config |
| **Web app (SPA/frontend)** | `package.json` with react/vue/svelte/angular; `vite.config`, `next.config`, `angular.json`, `svelte.config` |
| **Backend / API** | express/fastify/nest in `package.json`; `requirements.txt`/`pyproject.toml` with django/flask/fastapi; `Gemfile` with rails; `pom.xml`/`build.gradle` with spring |
| **Game** | Unity (`Assets/`, `ProjectSettings/`, `*.unity`); Unreal (`*.uproject`, `Content/`); Godot (`project.godot`); love2d/pygame sources |
| **Android app** | `AndroidManifest.xml` + `build.gradle` + `app/src/main/` |
| **iOS app** | `*.xcodeproj`/`*.xcworkspace`, `Info.plist`, `Podfile`, `.swift` sources |
| **Cross-platform mobile** | Flutter (`pubspec.yaml` + `lib/`); React Native (`package.json` + `android/` + `ios/`) |
| **Desktop (cross-platform)** | Electron (`electron` in `package.json`); Tauri (`src-tauri/`) |
| **Windows app** | `*.sln`, `*.csproj`, `*.vcxproj`; WPF/WinForms |
| **Linux/native app** | `CMakeLists.txt`/`Makefile` + GTK/Qt; `.desktop` entry |
| **Rust project** | `Cargo.toml` (bin vs lib from `src/main.rs` vs `src/lib.rs`) |
| **Go project** | `go.mod` (cmd/ for binaries) |
| **Python package** | `pyproject.toml`/`setup.py` + a package dir with `__init__.py` |
| **Library / package** | manifest declares a library (no app entrypoint), publishing config present |
| **Monorepo** | multiple manifests under `packages/`/`apps/`; workspaces in `package.json`/`pnpm-workspace.yaml` |
| **Containerized** | `Dockerfile`/`docker-compose.*` — note it as deployment, not the primary type |

Tie-breakers:
- Framework manifest present → it's an app/library, not a static site.
- Both `android/` and `ios/` under one JS project → cross-platform mobile.
- Several independent manifests in subtrees → monorepo; classify each workspace.
