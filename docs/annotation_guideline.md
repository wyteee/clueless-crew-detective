# Annotation Guideline v0.9 (Clueless Crew)

对象：清洗后、带段落编号 `[0001]` 的单篇文本（data/processed）。raw 文件不改。

## 流程
0. **先筛 reveal 位置**：从结尾往前读，找到 reveal 段，由程序算 reveal_pct。若不在 80% 之后（常见于"先抓获、后长篇解释/自白/往事回顾"的结构），只填 culprit、reveal_para_idx、reveal_quote 和 notes，排除原因由程序填 `other:reveal_before_80pct`，停止标注，不标 aliases。
1. 通读一遍（不要边读边填表）。读时在草稿上记：reveal 段号、所有角色称呼。
2. 判断是否合格：**至少有一个可识别的人类罪犯，且能确定主犯**。不合格 → 填 `exclusion_reason`，停止标注。
   - 有从犯但主犯明确 → 合格（见 culprit 字段）；多个罪犯地位相当、无法确定主犯 → `multiple_culprits`。
   - 取值：`multiple_culprits` / `non_criminal` / `unresolved` / `non_human` / `culprit_unnamed` / `other:<说明>`
   - 原书是图片（密码、图示），Gutenberg 版换成了文字，因而在 reveal 前泄露罪犯身份 → `other:cipher_text_leak`（如 M06 跳舞小人）。
3. 合格 → 填 culprit、reveal、aliases、culprit_before_reveal。

## 字段定义
- **culprit**：文本最终认定的罪犯，用全名（文中最完整的形式）。罪犯已死也照标。"crime"包括谋杀、盗窃、欺诈等，须在 notes 写明罪行类型。
  - 是否算 crime 不看是否违法：只要文本把某人的欺骗、迫害等行为当作谜底揭露出来，就算（如 P4，原文说"不违法"，但 Windibank 是被揭露的作恶者）。`non_criminal` 只用于没有任何人作恶的故事（误会、意外等）。
  - 多个罪犯：凡原文**明确**把罪行或参与归到某人身上的都要标，用 `; ` 分隔，**主犯放第一个**（如 `John Clay; Archie`）。
  - 有人被杀时，**动手杀人的人是主犯**，策划者、雇主、包庇者都算从犯（如 M21 Oberstein 而非 Walter，M28 Hayes 而非 Wilder）。
  - 只是知情、配合但原文没有明确归罪的人（如 P5 的 Rucastle 太太、Toller 夫妇）不标，写进 notes。
  - 原文没有给名字的从犯写作 `[unnamed: <描述>]`（如 P4 `[unnamed: Mary's mother]`）。
- **reveal_para_idx**：**第一次明确**把该人指认为罪犯的段落编号。有多个罪犯时，以**主犯**被抓获/暴露的那段为准。
  - ✓ 明确：叙述者/侦探直接点名并指认其罪行（"It was X who…"、当场抓获并宣布）。
  - ✗ 不算：怀疑、暗示、"我想可能是"、读者能猜到但文中未点破。
  - 若指认跨多段，取**第一个**满足"明确"的段。
  - 若罪犯先被当场抓获/暴露、之后才解释经过，以**暴露场景中文本第一次把罪行归到此人身上**的那段为准（可以是侦探的断言或评语），不必等到后面解释作案手法的段落；在 notes 记录判断理由。例：P1 取 [0245] "the schemer falls into the pit which he digs for another"，而不是解释手法的 [0248]。
  - 作者借别人之口或情节衔接点出罪犯名字，也算明确指认（如 M01 [0185] Watson 说 "The culprit is—"，[0186] 侍者通报 "Mr. John Turner"，取 [0186]）。这样 reveal 之前的文本不会含有这种点名。
- **reveal_quote**：该段内起决定作用的原句（原文抄录）。
- **aliases**：JSON，`{"规范名": ["称呼1","称呼2",...]}`；**所有罪犯（主犯和从犯）都要填**，另加主要嫌疑人/重要角色。包含全名、姓、名、头衔+姓、假名/化名。
  - 只收名字类称呼。只有头衔或职业、不带名字的称呼（如 P1 的 "the Doctor"）歧义太大，不收；"my stepfather" 这类相对于说话人的关系描述也不收。
  - 化名：只要原文说明了化名和真名是同一人（不论在 reveal 之前还是之后），就把化名并入此人名下（如 P2 "Vincent Spaulding" 并入 John Clay，P4 "Hosmer Angel" 并入 James Windibank）。若这个联系只在 reveal 及之后才说明，在 notes 写明出处段号。
    每个化名/误称联系另在 `manifest/alias_links.csv` 记一行（`story_id, character, forms, link_para_idx, link_quote`），reveal 前说明的也要记（如 P3 "John Robinson" [0169]）；代码据此生成"只用 reveal 前证据"的版本。
  - 收入的称呼本身须在 reveal 段之前出现过。若同一称呼会匹配到别人（如 P1 中 "Roylott" 也匹配 Helen 的 "Miss Roylott"），在 notes 记录。
  - 未具名的从犯没有名字可收，aliases 留空列表（如 P4 `"[unnamed: Mary's mother]": []`），不要用 "mother" 这类有歧义的称呼。
- **culprit_before_reveal**：`yes` 若**主犯**的任一 alias 在 reveal 段之前出现过，否则 `no`。
- **reveal_pct**：程序计算，不要手填。
  - 若 reveal 不在全文 80% 之后（`reveal_para_idx ≤ 0.8 × 总段数`），80% 前缀会含揭晓，故事排除：程序自动填 `exclusion_reason = other:reveal_before_80pct`。罪犯、reveal 等字段照常保留作记录。
- **annotator**：标注者姓名；交叉复核时复核者另起一行，story_id 相同，annotator 不同。

## 一致性规则
- 段号按文件里的 `[xxxx]` 为准；标题行、章节号行也占段号，不要手工重排。
- reveal 差 ≤2 段视为"近似一致"，> 2 段需讨论并把结论写回本规范。
- 每次修改规范，版本号 +0.1 并在下方记录。

## 变更记录
- v0.1 初稿，待 P1 交叉复核后修订。
- v0.2（2026-10-04，P1 标注后）：明确"先暴露、后解释"时取暴露场景中第一次把罪行归到此人的段落（P1 取 [0245]，不取 [0248]）；aliases 只收名字类称呼，不收关系描述，同名冲突记入 notes。
- v0.3（2026-10-04，P2–P5 标注后）：允许多个罪犯，全部标出，主犯放第一个，reveal 与 culprit_before_reveal 以主犯为准；只有无法确定主犯时才用 `multiple_culprits`。所有罪犯都标 aliases；原文说明过的化名并入真名（联系在 reveal 之后才说明时记出处）；未具名从犯 aliases 留空；是否算 crime 不看是否违法，`non_criminal` 只用于无人作恶的故事。
- v0.4（2026-10-04，alias 检查后）：不收只有头衔、不带名字的称呼（P1 删去 "the Doctor"）；化名/误称联系统一记入 `manifest/alias_links.csv`（段号 + 引文）。
- v0.5（2026-10-04，M01 标注后）：作者借他人之口/情节衔接点出罪犯名字也算明确指认（M01 取 [0186]，不取侦探断言的 [0192]）。
- v0.6（2026-10-04，M03/M04 标注后）：reveal 不在全文 80% 之后的故事排除，`other:reveal_before_80pct` 由程序填写（M03、M04）。
- v0.7（2026-10-05，M06 标注后）：原书图片被换成文字、提前泄露罪犯的故事排除，`other:cipher_text_leak`（M06）。
- v0.8（2026-10-05，M01–M06 后）：标注前先筛 reveal 位置，80% 之前揭晓的只记罪犯和 reveal、不标 aliases（"先抓获后长篇解释"结构很常见）。
- v0.9（2026-10-05，筛选后）：有人被杀时，动手杀人者为主犯（M21 Oberstein、M28 Hayes、R05 Antonelli）。
