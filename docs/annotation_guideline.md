# Annotation Guideline v0.1 (Clueless Crew)

对象：清洗后、带段落编号 `[0001]` 的单篇文本（data/processed）。raw 文件不改。

## 流程
1. 通读一遍（不要边读边填表）。读时在草稿上记：reveal 段号、所有角色称呼。
2. 判断是否合格：**有且仅有一个可识别的人类罪犯**。不合格 → 填 `exclusion_reason`，停止标注。
   - 取值：`multiple_culprits` / `non_criminal` / `unresolved` / `non_human` / `culprit_unnamed` / `other:<说明>`
3. 合格 → 填 culprit、reveal、aliases、culprit_before_reveal。

## 字段定义
- **culprit**：文本最终认定的罪犯，用全名（文中最完整的形式）。罪犯已死也照标。"crime"包括谋杀、盗窃、欺诈等，须在 notes 写明罪行类型。
- **reveal_para_idx**：**第一次明确**把该人指认为罪犯的段落编号。
  - ✓ 明确：叙述者/侦探直接点名并指认其罪行（"It was X who…"、当场抓获并宣布）。
  - ✗ 不算：怀疑、暗示、"我想可能是"、读者能猜到但文中未点破。
  - 若指认跨多段，取**第一个**满足"明确"的段。
  - 若罪犯先被当场抓获/暴露、之后才解释经过，以"身份与罪行被明确指认"的那段为准，并在 notes 记录判断理由。
- **reveal_quote**：该段内起决定作用的原句（原文抄录）。
- **aliases**：JSON，`{"规范名": ["称呼1","称呼2",...]}`；**只需为罪犯和主要嫌疑人/重要角色填写**，包含全名、姓、名、头衔+姓、假名/化名。注明化名是否在 reveal 之前已出现。
- **culprit_before_reveal**：`yes` 若罪犯的任一 alias 在 reveal 段之前出现过，否则 `no`。
- **reveal_pct**：程序计算，不要手填。
- **annotator**：标注者姓名；交叉复核时复核者另起一行，story_id 相同，annotator 不同。

## 一致性规则
- 段号按文件里的 `[xxxx]` 为准；标题行、章节号行也占段号，不要手工重排。
- reveal 差 ≤2 段视为"近似一致"，> 2 段需讨论并把结论写回本规范。
- 每次修改规范，版本号 +0.1 并在下方记录。

## 变更记录
- v0.1 初稿，待 P1 交叉复核后修订。
