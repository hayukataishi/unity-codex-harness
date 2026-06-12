# Scene別設計

Sceneを追加するときは`_template/`を`<scene-key>/`へ複製し、次を守ります。

- directory名: ASCII kebab-case。例: `main-game`
- AC prefix: `SCENE-MAIN-GAME-AC-`
- `acceptance.md`: Playerから観察できるScene単位の要求
- `design.md`: Scene構成、遷移、Hierarchy、依存、実装マッピング
- Additive Sceneは、UI、lighting、bootstrapなど責務ごとに別Sceneとして扱う。
- Sceneを跨ぐ要求は`../all/acceptance.md`へ置く。
