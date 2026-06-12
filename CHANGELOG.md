# Changelog

このファイルはUnity Codex Harnessの公開版ごとの変更を記録する。
版番号は[Semantic Versioning 2.0.0](https://semver.org/)に従う。

## [0.1.0] - 2026-06-12

初回versioned release。

### Added

- Unity設計、実装、検証、gameplay review、報告用のCodex Skills
- Installerのownership、manifest、backup、migration bundle
- harness-managed完全性検査とproject-owned override
- Unity 6.4 fixture、Python回帰、GameCI定義
- マイルストーン別初期設計対話とdesign readiness検査
- 機械可読なrelease metadata、互換性matrix、migration policy
- 再現可能ZIP、release manifest、SHA-256 checksumの生成

### Changed

- 評価レポートをsource-onlyとし、導入先ゲームへの配布対象から除外
- `harness.lock.json`をharness-managed標準pinへ変更
- repository-scoped Skillの正本と導入先をCodex標準の
  `.agents/skills/`へ変更
- 旧`.codex/skills/`の未改変Harness Skillをbackup付きで安全に退役

### Migration

- `UNRELEASED`版からの更新手順は
  [release契約の移行ガイド](docs/unity_harness_release.md#v010-migration)を参照

[0.1.0]: https://github.com/hayukataishi/unity-codex-harness/releases/tag/v0.1.0
