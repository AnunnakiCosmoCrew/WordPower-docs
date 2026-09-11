# ADR 0001 — Swift Package Manager replaces CocoaPods for iOS native dependencies

**Status:** Accepted
**Date:** 2026-09-11
**Deciders:** @mertyertugrul
**Tracking:** WordPower-app#1047 · PR WordPower-app#1049
**Supersedes:** the CocoaPods-based iOS build, and the WP-959 `Podfile.lock` sync guard

> First entry in `adr/`. Earlier decision records live under `docs/architecture/`
> (e.g. `ROOT_FAMILIES_DECISION.md`).

## Context

The iOS app's native dependencies (Firebase, Sentry, Google Sign-In, and the Flutter
plugins' platform code) were resolved through CocoaPods: `ios/Podfile` +
`ios/Podfile.lock`, with a Linux CI guard (WP-959, `ios-podlock-sync.yml`) that
compared `Podfile.lock` against `pubspec.lock`.

Three things converged in September 2026:

1. **Firebase is leaving CocoaPods.** `pod install` warns that FirebaseCore is
   deprecated there in favour of Swift Package Manager, and *"new versions will no
   longer be published to CocoaPods after October 2026."* Existing versions keep
   installing, but the first `firebase_*` bump needing a newer Firebase iOS SDK
   would fail `pod install`.
2. **Flutter already switched.** Swift Package Manager has been Flutter's default iOS
   dependency manager since 3.44 (`enabledByDefault: true` on stable in
   `flutter_tools` `features.dart`; it was opt-in on 3.41). CI moved onto that
   default when the pin went 3.41.6 → 3.44.4 (WordPower-app#1016).
3. **Local and CI had silently diverged.** The main dev machine had
   `enable-swift-package-manager: false` in its global Flutter config, so local iOS
   builds resolved everything through CocoaPods while CI's next build would migrate
   the Xcode project to SPM mid-build. `deploy-ios.yml` is manual and had not run
   since 2026-06-06, so the first SPM TestFlight build would have been untested.

Plugin readiness was audited at the locked versions: every plugin with native iOS
code ships an iOS `Package.swift` (the four Firebase plugins, sentry_flutter,
audioplayers_darwin, share_plus, package_info_plus, url_launcher_ios,
shared_preferences_foundation, sign_in_with_apple, google_sign_in_ios, plus the
SDK's integration_test). The two packages without one have no native iOS code:
`path_provider_foundation` is a Dart-only (`dartPluginClass`) plugin and
`sqlite3_flutter_libs` 0.6.0+eol is an empty end-of-life shim. Flutter confirmed it
on the first migrated build: *"All plugins found for ios are Swift Packages."*

## Decision

**Use Swift Package Manager exclusively for iOS native dependencies, and remove
CocoaPods from the project.**

- `frontend/pubspec.yaml` pins `flutter: config: enable-swift-package-manager: true`.
  Flutter resolves feature flags as *environment variable > project manifest >
  global config*, so the project — not each machine's global setting — decides.
- `Runner.xcodeproj` carries Flutter's SPM integration
  (`FlutterGeneratedPluginSwiftPackage` local package + "Prepare Flutter Framework
  Script" scheme pre-action), committed so CI no longer migrates it mid-build.
- CocoaPods is gone: `pod deintegrate`, `Podfile` / `Podfile.lock` deleted, the
  `Pods.xcodeproj` reference removed from `Runner.xcworkspace`, and the optional
  `Pods/…xcconfig` includes removed from `Flutter/{Debug,Release}.xcconfig`.
  `Runner.xcworkspace` remains (fastlane's `build_app` archives it).
- Both `Package.resolved` copies are committed (workspace and bare project), as
  Flutter's app template expects — the SPM equivalent of `Podfile.lock`.
- The WP-959 guard is replaced by `tool/check_ios_spm_resolved_sync.py` /
  `ios-spm-resolved-sync.yml` (informational, Linux, stdlib-only).

## Why the guard changes purpose

Under SPM each plugin's `Package.swift` pins its native SDK **exactly**
(`firebase_core` 4.14.0 → `firebase-ios-sdk` `exact: "12.18.0"`; `sentry_flutter`
9.30.0 → `sentry-cocoa` `exact: "8.58.4"`), and Flutter does not pass
`-onlyUsePackageVersionsFromResolvedFile` to `xcodebuild`. So the WP-959 failure mode
— a stale lock pinning an old native SDK and killing the deploy at `pod install`
(#958) — cannot recur: Xcode re-resolves instead.

The successor guard therefore protects the lock's *honesty*, not the build:

1. every `exact:` native pin a plugin declares matches `Package.resolved`;
2. every native iOS plugin ships an iOS `Package.swift` — the one failure mode SPM
   introduces, since there is no CocoaPods to fall back to;
3. the two `Package.resolved` copies agree on **version and revision** — two copies
   that both say `12.18.0` but point at different commits are not in sync (raised in
   Copilot's review of PR #1049);
4. the SwiftPM wiring stays intact and CocoaPods stays gone: `Runner.xcodeproj`
   references `FlutterGeneratedPluginSwiftPackage`, the scheme runs the *Prepare
   Flutter Framework Script* pre-action, and there is no `ios/Podfile`, `[CP]` build
   phase or `Pods` framework. Without that wiring the committed `Package.resolved`
   is not what gets built.

Range-resolved transitive pins (15 of the 17 today, e.g. GoogleSignIn,
GoogleUtilities, gRPC, leveldb) are not compared: for those the committed
`Package.resolved` *is* the source of truth, which is why it is committed.

## Consequences

**Positive**

- Firebase iOS SDK releases after October 2026 remain reachable.
- One dependency manager, matching Flutter's default and its documented direction
  (*"Support for disabling it will be removed in a future release"*).
- Local, CI and TestFlight builds resolve the same way, independent of anyone's
  global Flutter config.
- No Ruby/CocoaPods toolchain is needed for iOS dependencies (Ruby remains for
  fastlane via `ios/Gemfile`), and `e2e-ios.yml` drops its CocoaPods spec-repo cache
  and `pod install --repo-update` step.

**Negative / costs**

- A future plugin without an iOS `Package.swift` cannot be adopted without
  reintroducing CocoaPods. The successor guard flags this on the PR that adds it.
- Dependabot still cannot run Xcode, so after a Firebase or Sentry plugin bump
  `Package.resolved` must be regenerated on macOS; the guard reports it with the
  command.
- First SPM resolution is slow (≈160 s locally for the Firebase SDK); CI caching of
  the SwiftPM source-packages directory is a possible follow-up once timings are
  measured.

## Alternatives considered

1. **Keep CocoaPods; opt out via `enable-swift-package-manager: false`.** Aligns CI
   with local immediately, but only buys time: Flutter states the opt-out will be
   removed, and post-October-2026 Firebase SDKs won't reach CocoaPods.
2. **SPM on, CocoaPods kept as a fallback (hybrid).** Aligns local and CI, but keeps
   two dependency managers and two lockfiles to reason about, with no current plugin
   needing the fallback.
3. **Full SPM, CocoaPods removed — chosen.** Possible because every native plugin is
   SPM-ready, and it leaves one mechanism to maintain and verify.

## Verification

Run with Flutter 3.47.3 / Xcode 26.6 on macOS during WordPower-app#1047:

- First migrated build: Flutter added SPM integration and fetched packages; confirmed
  all plugins are Swift Packages.
- After CocoaPods removal (no `Podfile` present): `flutter build ios --simulator
  --debug` ✓.
- `flutter build ios --release --no-codesign` — the exact command `deploy-ios.yml`
  runs: ✓ — `Runner.app` 36.7 MB, built with no `Podfile` present.
- `Package.resolved` pins `firebase-ios-sdk` 12.18.0 and `sentry-cocoa` 8.58.4 —
  identical to what the CocoaPods lock carried, so the SPM path ships the same native
  versions.
- **Stale-lock experiment** (the #958 failure mode): both `Package.resolved` copies were
  pinned back to `firebase-ios-sdk` 12.17.0 using its real revision (`33a468ad`) while
  the plugins still required `exact: 12.18.0`. `flutter build ios` **succeeded** —
  and the SwiftPM source checkout it compiled was at tag **12.18.0** (`346daa9f`), not
  the stale pin. Xcode re-resolved to the plugins' exact requirement instead of failing,
  which is why the successor guard protects the lock's honesty rather than the build.
  The guard itself exited 1 on that stale lock, with one finding per Firebase plugin.
- Successor guard: exits 0 on the committed state and exits 1 on each of 11 failure
  cases — stale version; copies disagreeing on version; copies agreeing on version
  but not revision; a native plugin without `Package.swift`; missing
  `.flutter-plugins-dependencies` or `Package.resolved`; a reintroduced `Podfile`; a
  project without `FlutterGeneratedPluginSwiftPackage`; a `[CP]` build phase; a scheme
  without the SPM pre-action; a missing `project.pbxproj`.
- `e2e-ios.yml` on CI's macOS 15 runner (run 34591352096): Xcode fetched the SwiftPM
  dependencies, no `pod install` ran, and the simulator smoke test passed — a second
  environment beyond the local Xcode 26.6 builds.

## References

- Firebase: https://firebase.google.com/docs/ios/cocoapods-deprecation
- Flutter: https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-app-developers
- Flutter 3.44 release notes — "Swift Package Manager is now the default for iOS and macOS"
- WordPower-app#958 (CocoaPods lock drift broke TestFlight), WP-959 (the original guard),
  #1016 / #1046 (Flutter pin bumps), #1047 (this change)
