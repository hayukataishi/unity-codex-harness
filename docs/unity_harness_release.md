<!-- UNITY_CODEX_HARNESS_RELEASE: VERSIONED AND HARNESS-MANAGED -->

# Unity Codex Harness Release契約

> **所有者: Unity Codex Harness**
>
> この文書は、導入済みProjectが使用中のHarness版、互換性、
> 更新時のmigration policyを説明する`harness-managed`文書です。
> 機械可読な正本は`../harness.release.json`です。

## Current release

| 項目 | 値 |
|---|---|
| Harness version | `0.1.0` |
| Git tag | `v0.1.0` |
| Channel | `stable` |
| Release date | `2026-06-12` |
| Install manifest schema | `2` |
| Artifact | `unity-codex-harness-0.1.0.zip` |
| Checksums | `SHA256SUMS` |

Installerは`.unity-codex-harness/install-manifest.json`へversion、tag、
`harness.release.json`のSHA-256を記録する。導入済みProjectの契約版は、
Git branch名やclone時刻ではなく、この3項目で識別する。

## Compatibility matrix

`PASS`は表のtested exact versionで実行証拠があることを表す。
同じcompatibility band内でも、未記載のpatch versionを自動的に
検証済みとは扱わない。

| 対象 | Compatibility band | Tested exact version | 状態 |
|---|---|---|---|
| Codex CLI | `0.137.x` | `0.137.0` | `PASS` |
| Codex IDE | `0.137.x` | なし | `NOT RUN` |
| Codex App | `0.137.x` | なし | `NOT RUN` |
| Unity Editor | `6000.4.x` | `6000.4.10f1` | fixture `PASS` |
| Python | `3.11+` | CI `3.11` | `PASS` |

Compatibility band外へ更新する場合は、release metadata、fixture、
外部依存pin、Installer回帰、Unity実行証拠を同じrelease候補で再検証する。

<a id="migration-policy"></a>
## Migration policy

- VersionはSemantic Versioningを使用する。
- `PATCH`は互換性を壊さない修正と文書改善に使用する。
- `MINOR`は既存Projectを自動または明示手順で移行できる能力追加に使用する。
- `MAJOR`はinstall manifest、ownership、必須契約、配置、Skill APIなどの
  互換性を自動維持できない変更に使用する。
- `0.x`期間も破壊的変更を黙って配布せず、migration guideとbackup手順を付ける。
- Installerはproject-ownedファイルを自動上書きしない。
- harness-managed競合は書込み前に停止し、承認された`--force-file`または
  `--force`だけをbackup後に適用する。
- project-owned template変更は`--prepare-migration`で三者比較bundleを作る。
- migrationを伴うreleaseは、対応可能な移行元versionと手順を
  `harness.release.json`と本書へ記録する。
- downgradeは自動実行しない。必要な場合はbackupから復元し、対象releaseの
  Installerで完全性を再検証する。

<a id="v010-migration"></a>
## v0.1.0 migration

対象: `harness.release`が`UNRELEASED`だった導入済みProject。

1. ゲームProjectとHarness checkoutの変更をcommitまたはbackupする。
2. `v0.1.0`のrelease artifactと`SHA256SUMS`を取得し、archive hashを照合する。
3. 新しいHarnessから`python3 scripts/install.py <PROJECT> --dry-run`を実行する。
4. 旧project-owned `harness.lock.json`に差分がある場合は
   `--prepare-migration`で標準pinとoverrideを分離する。
5. harness-managed競合は差分を確認し、承認したpathだけ
   `--force-file <PATH>`で更新する。
6. project-owned template更新はmigration bundleから必要な変更だけを統合する。
7. `python3 scripts/install.py <PROJECT> --check`を実行する。
8. install manifestの`harness.release`が`0.1.0`、`releaseTag`が`v0.1.0`
   であることを確認する。

旧版で配布されたsource-only評価レポートは、旧manifestのsource hashと
一致する場合だけbackup後に退役する。ローカル変更済みの場合は削除せず停止する。

旧`.codex/skills/`に配布されたHarness Skillも同様に、旧manifestで
`harness-managed`かつ実ファイルhash一致の場合だけbackup後に退役し、
`.agents/skills/`へ再配置する。ローカル変更、symlink、所有記録なし、
manifest不整合がある場合は、重複Skillを残したまま続行せず書き込み前に停止する。
旧配置のproject-owned外部Skillは自動移動せず、上流と内容を確認して
`.agents/skills/`へ手動移行し、旧コピーを除去してからInstallerを再実行する。

## Release artifact verification

Release archiveは固定timestamp、sorted path、固定permissionで生成する。

```bash
python3 scripts/build_release.py --check --tag v0.1.0
python3 scripts/build_release.py --output Artifacts/Releases/v0.1.0
(cd Artifacts/Releases/v0.1.0 && shasum -a 256 -c SHA256SUMS)
```

GitHub Releaseにはarchive、`release-manifest.json`、`SHA256SUMS`を添付する。
Source archiveだけでなくchecksum付きHarness artifactを配布単位とする。
