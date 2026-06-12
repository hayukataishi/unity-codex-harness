# 共通Prefab設計

複数Sceneから利用するPrefabごとに`<prefab-key>.md`を作成します。

```markdown
### PREFAB-001: <名称>
**状態:** Draft / Approved / 廃止
**上流AC:** `GAME-AC-001` または `SCENE-...-AC-001`
**仕様**
<責務、Root Component、serialized reference、variant方針>
#### 実装マッピング
| Unity単位 | Path | Symbol / Hierarchy | 状態 |
|---|---|---|---|
| Prefab | `Assets/.../<Name>.prefab` | `<Root>` | Planned |
```
