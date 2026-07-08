# -*- coding: utf-8 -*-
"""把 data/akp_flow_dump.json 生成为 Cursor Canvas（单文件 .canvas.tsx，数据内联）。

用法：python backend/scripts/build_akp_canvas.py
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DUMP = PROJECT_ROOT / "data" / "akp_flow_dump.json"
CANVAS = Path(
    r"C:\Users\congw\.cursor\projects"
    r"\e-HuaweiMoveData-Users-congw-Desktop-go-work-StoryForge\canvases\akp-flow-review.canvas.tsx"
)

TEMPLATE = r'''import {
  Stack, Row, Grid, Card, CardHeader, CardBody,
  H1, H2, H3, Text, Code, Pill, Stat, Table, Callout, Divider,
  CollapsibleSection, useHostTheme, useCanvasState,
} from "cursor/canvas";

const DATA: any = /*__DATA__*/ null;

const TABS: { id: string; label: string }[] = [
  { id: "overview", label: "总览" },
  { id: "akp", label: "AKP 证据包" },
  { id: "extract", label: "提取 Agent" },
  { id: "opening", label: "开局 Agent" },
  { id: "action", label: "行动链路" },
  { id: "summary", label: "战报 Agent" },
];

const SCORE_LABELS: Record<string, string> = {
  rule_consistency: "规则一致",
  world_consistency: "世界一致",
  context_continuity: "上下文连贯",
  character_alignment: "角色贴合",
  npc_knowledge_boundary: "NPC 知识边界",
  clue_progression: "线索推进",
};

function Mono({ text, max = 340 }: { text: string; max?: number }) {
  const t = useHostTheme();
  return (
    <div style={{
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: 12, lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word",
      background: t.fill.tertiary, color: t.text.secondary, padding: 12,
      borderRadius: 6, maxHeight: max, overflow: "auto",
      border: "1px solid " + t.stroke.tertiary,
    }}>{text}</div>
  );
}

function KV({ k, v }: { k: string; v: any }) {
  return (
    <Row gap={10} align="start">
      <div style={{ minWidth: 132, flexShrink: 0 }}>
        <Text size="small" tone="tertiary">{k}</Text>
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {typeof v === "string" ? <Text size="small">{v}</Text> : v}
      </div>
    </Row>
  );
}

function Chips({ items }: { items: any[] }) {
  if (!items || !items.length) return null;
  return (
    <Row gap={6} wrap>
      {items.map((s, i) => <Pill key={i} size="sm">{String(s)}</Pill>)}
    </Row>
  );
}

function IOColumns({ left, right, leftTitle, rightTitle }:
  { left: any; right: any; leftTitle: string; rightTitle: string }) {
  return (
    <Grid columns="1fr 1fr" gap={14} align="start">
      <Card>
        <CardHeader>{leftTitle}</CardHeader>
        <CardBody><Stack gap={10}>{left}</Stack></CardBody>
      </Card>
      <Card>
        <CardHeader>{rightTitle}</CardHeader>
        <CardBody><Stack gap={10}>{right}</Stack></CardBody>
      </Card>
    </Grid>
  );
}

function Overview() {
  const a = DATA.agents;
  const seeded = a.opening.seeded_facts_by_type || {};
  const seededTotal = Object.keys(seeded).reduce((n, k) => n + seeded[k].length, 0);
  const rbFacts = a.rulebook_extractor.output.public_world_facts || [];
  const withRef = rbFacts.filter((f: any) => f.source_ref).length;
  const rows = [
    ["RulebookExtractor", "PHB → 规则事实/世界基调",
      a.rulebook_extractor.tokens_used, a.rulebook_extractor.latency_ms,
      rbFacts.length + " facts"],
    ["ModuleExtractor", "模组 → 场景/隐藏真相/NPC",
      a.module_extractor.tokens_used, a.module_extractor.latency_ms,
      (a.module_extractor.output.scenes || []).length + " 场景 / " +
      (a.module_extractor.output.hidden_truths || []).length + " 真相"],
    ["OpeningAgent", "开局叙事 + 灌入会话",
      a.opening.tokens_used, a.opening.latency_ms, seededTotal + " facts 落库"],
    ...a.narrative.map((n: any, i: number) => [
      "Narrative+Critic #" + (i + 1), n.player_action,
      n.meta.tokens_used, n.meta.latency_ms,
      "审核 " + n.ai_review.overall_score + " 分",
    ]),
    ["SummaryAgent", "本局战报", a.summary.tokens_used, a.summary.latency_ms,
      a.summary.output.ending_type],
  ];
  const avg = Math.round(
    a.narrative.reduce((s: number, n: any) => s + n.ai_review.overall_score, 0) /
    a.narrative.length);

  return (
    <Stack gap={16}>
      <Callout tone="success" title="AKP 数据溯源已确认">
        规则书/模组均经 AKP 建包检索，证据包含 <Code>## References</Code> 指向 <Code>references/…/chunks</Code>；
        规则事实中 {withRef}/{rbFacts.length} 条带 <Code>source_ref</Code> 出处；开局按会话灌入 {seededTotal} 条 facts。
        所有 agent 输出均通过后端 DTO 校验。
      </Callout>

      <Grid columns={4} gap={12}>
        <Stat value={rbFacts.length} label="规则世界事实" />
        <Stat value={(a.module_extractor.output.scenes || []).length} label="模组场景" />
        <Stat value={(a.module_extractor.output.hidden_truths || []).length} label="隐藏真相" tone="warning" />
        <Stat value={seededTotal} label="开局灌入 facts" tone="info" />
        <Stat value={(a.opening.seeded_npcs || []).length} label="灌入 NPC" />
        <Stat value={a.narrative.length} label="行动回合" />
        <Stat value={avg} label="审核均分" tone="success" />
        <Stat value={DATA.meta.akp_bundle_preset} label="AKP 预设" />
      </Grid>

      <H2>各 Agent 运行概览</H2>
      <Table
        headers={["Agent", "职责 / 输入", "tokens", "延迟(ms)", "产出"]}
        columnAlign={["left", "left", "right", "right", "left"]}
        rows={rows.map((r) => [
          <Text size="small" weight="semibold">{r[0]}</Text>,
          <Text size="small" tone="secondary">{String(r[1]).slice(0, 40)}</Text>,
          String(r[2]), String(r[3]),
          <Text size="small">{r[4]}</Text>,
        ])}
      />
    </Stack>
  );
}

function AkpView() {
  const packs = [
    { key: "rulebook_pack", title: "规则书知识包 · PHB" },
    { key: "module_pack", title: "模组知识包 · 追捕克仑可" },
  ];
  return (
    <Stack gap={18}>
      <Text tone="secondary">
        以下是喂给提取 Agent 的真实证据包（<Code>kbtool bundle</Code> 确定性检索产出，无 LLM 参与）。
        每条证据都带 <Code>references/</Code> 出处，可回跳原文校验。
      </Text>
      {packs.map((p) => {
        const pack = DATA.akp[p.key];
        return (
          <Stack gap={8} key={p.key}>
            <H2>{p.title}</H2>
            <Text size="small" tone="tertiary" truncate="start">{pack.pack_dir}</Text>
            {pack.bundles.map((b: any, i: number) => (
              <CollapsibleSection
                key={i}
                title={b.question}
                count={b.references ? b.references.length : 0}
                defaultOpen={i === 0}
                trailing={<Pill size="sm" active={b.verify_ok}>hits {b.hits}</Pill>}
              >
                <Stack gap={8}>
                  {b.references && b.references.length ? (
                    <Chips items={b.references.map((r: string) =>
                      r.replace("references/", "").replace(/^[^/]+\//, ""))} />
                  ) : null}
                  <Mono text={b.bundle_md} max={420} />
                </Stack>
              </CollapsibleSection>
            ))}
          </Stack>
        );
      })}
    </Stack>
  );
}

function FactTable({ facts }: { facts: any[] }) {
  if (!facts || !facts.length) return null;
  return (
    <Table
      headers={["内容", "重要度", "出处 (source_ref)"]}
      columnAlign={["left", "left", "left"]}
      rows={facts.map((f: any) => [
        <Text size="small">{f.content}</Text>,
        <Pill size="sm">{f.importance || "normal"}</Pill>,
        f.source_ref
          ? <Code>{f.source_ref.replace("references/", "")}</Code>
          : <Text size="small" tone="quaternary">—</Text>,
      ])}
    />
  );
}

function ExtractView() {
  const rb = DATA.agents.rulebook_extractor;
  const mod = DATA.agents.module_extractor;
  return (
    <Stack gap={20}>
      <Stack gap={8}>
        <H2>RulebookExtractor（PHB）</H2>
        <IOColumns
          leftTitle="输入"
          left={<>
            <KV k="来源" v={rb.input.source_name} />
            <KV k="focus" v={rb.input.focus} />
            <KV k="模式" v={<Pill size="sm" active>{rb.input.mode}</Pill>} />
            <KV k="tokens / 延迟" v={rb.tokens_used + " / " + rb.latency_ms + "ms"} />
          </>}
          rightTitle="输出"
          right={<>
            <KV k="title" v={rb.output.title} />
            <KV k="world_style" v={rb.output.world_style} />
            <KV k="world_setting" v={<Mono text={rb.output.world_setting} max={180} />} />
          </>}
        />
        <H3>public_world_facts（带 AKP 出处）</H3>
        <FactTable facts={rb.output.public_world_facts} />
        {rb.output.core_rules_summary ? (
          <Card><CardHeader>core_rules_summary</CardHeader>
            <CardBody><Mono text={rb.output.core_rules_summary} max={220} /></CardBody></Card>
        ) : null}
      </Stack>

      <Divider />

      <Stack gap={8}>
        <H2>ModuleExtractor（追捕克仑可）</H2>
        <IOColumns
          leftTitle="输入"
          left={<>
            <KV k="来源" v={mod.input.source_name} />
            <KV k="module_title" v={mod.input.module_title} />
            <KV k="模式" v={<Pill size="sm" active>{mod.input.mode}</Pill>} />
            <KV k="tokens / 延迟" v={mod.tokens_used + " / " + mod.latency_ms + "ms"} />
          </>}
          rightTitle="输出概要"
          right={<>
            <KV k="title" v={mod.output.title} />
            <KV k="current_scene" v={<Code>{mod.output.current_scene}</Code>} />
            <KV k="story_summary" v={<Mono text={mod.output.story_summary} max={200} />} />
          </>}
        />
        <H3>场景图 scenes</H3>
        <Table
          headers={["scene_id", "标题", "出口 exits", "兴趣点"]}
          rows={(mod.output.scenes || []).map((s: any) => [
            <Code>{s.scene_id}</Code>,
            <Text size="small">{s.title}</Text>,
            <Text size="small" tone="secondary">{(s.exits || []).join(", ") || "—"}</Text>,
            <Text size="small" tone="secondary">{(s.points_of_interest || []).join(", ") || "—"}</Text>,
          ])}
        />
        <Grid columns="1fr 1fr" gap={14} align="start">
          <Stack gap={6}>
            <H3>隐藏真相 hidden_truths</H3>
            <Stack gap={4}>
              {(mod.output.hidden_truths || []).map((h: string, i: number) => (
                <Text key={i} size="small">· {h}</Text>
              ))}
            </Stack>
          </Stack>
          <Stack gap={6}>
            <H3>可见 NPC visible_npcs</H3>
            {(mod.output.visible_npcs || []).map((n: any, i: number) => (
              <Card key={i}>
                <CardHeader trailing={<Code>{n.npc_id}</Code>}>{n.name}</CardHeader>
                <CardBody><Stack gap={6}>
                  <Text size="small" tone="secondary">{n.personality || n.description}</Text>
                  <KV k="知识范围" v={<Chips items={n.knowledge_scope} />} />
                  <KV k="禁忌知识" v={<Chips items={n.forbidden_knowledge} />} />
                </Stack></CardBody>
              </Card>
            ))}
          </Stack>
        </Grid>
      </Stack>
    </Stack>
  );
}

function OpeningView() {
  const op = DATA.agents.opening;
  const seeded = op.seeded_facts_by_type || {};
  const order = ["world_public", "player_known", "npc_private", "hidden_truth"];
  const label: Record<string, string> = {
    world_public: "world_public（世界公开）",
    player_known: "player_known（玩家已知）",
    npc_private: "npc_private（NPC 私有）",
    hidden_truth: "hidden_truth（隐藏真相·锁定）",
  };
  return (
    <Stack gap={18}>
      <IOColumns
        leftTitle="输入（来自 AKP 规则书 + 模组）"
        left={<>
          <KV k="world.name" v={op.input.world.name} />
          <KV k="world.style" v={op.input.world.style} />
          <KV k="角色" v={op.input.character.name + " · " + op.input.character.profession} />
          <KV k="动机" v={op.input.character.motivation} />
          <KV k="public_world_facts" v={op.input.public_world_facts.length + " 条（注入）"} />
          <KV k="seed_npcs" v={<Chips items={(op.input.seed_npcs || []).map((n: any) => n.name)} />} />
          <KV k="opening_prompt" v={<Mono text={op.input.world.opening_prompt} max={160} />} />
        </>}
        rightTitle="输出（OpeningOutput）"
        right={<>
          <KV k="scene_title" v={<Text size="small" weight="semibold">{op.output.scene_title}</Text>} />
          <KV k="main_task" v={op.output.main_task} />
          <KV k="narration" v={<Mono text={op.output.narration} max={200} />} />
          <KV k="initial_clues" v={<Chips items={(op.output.initial_clues || []).map((c: any) => c.title || c.content)} />} />
          <KV k="npcs" v={<Chips items={(op.output.npcs || []).map((n: any) => n.name)} />} />
        </>}
      />

      <H2>world_seed 灌入会话的 facts（数据源自模组包）</H2>
      <Grid columns="1fr 1fr" gap={14} align="start">
        {order.filter((k) => seeded[k] && seeded[k].length).map((k) => (
          <Card key={k}>
            <CardHeader trailing={<Pill size="sm">{seeded[k].length}</Pill>}>{label[k]}</CardHeader>
            <CardBody><Stack gap={5}>
              {seeded[k].map((f: any, i: number) => (
                <Row key={i} gap={6} align="start">
                  {f.status === "locked"
                    ? <Pill size="sm">locked</Pill> : null}
                  <Text size="small">{f.content}</Text>
                </Row>
              ))}
            </Stack></CardBody>
          </Card>
        ))}
      </Grid>

      <H2>灌入的 NPC 人格与知识边界</H2>
      <Grid columns={2} gap={14}>
        {(op.seeded_npcs || []).map((n: any, i: number) => (
          <Card key={i}>
            <CardHeader trailing={<Code>{n.npc_id}</Code>}>{n.name}</CardHeader>
            <CardBody><Stack gap={6}>
              <Text size="small" tone="secondary">{n.personality}</Text>
              <KV k="知识范围" v={<Chips items={n.knowledge_scope} />} />
              <KV k="禁忌知识" v={<Chips items={n.forbidden_knowledge} />} />
            </Stack></CardBody>
          </Card>
        ))}
      </Grid>
    </Stack>
  );
}

function ScoreTable({ scores }: { scores: Record<string, number> }) {
  const keys = Object.keys(scores || {});
  if (!keys.length) return null;
  return (
    <Table
      headers={["评审维度", "分数"]}
      columnAlign={["left", "right"]}
      rows={keys.map((k) => [
        <Text size="small">{SCORE_LABELS[k] || k}</Text>,
        <Text size="small" weight="semibold">{scores[k]}</Text>,
      ])}
    />
  );
}

function ActionView() {
  return (
    <Stack gap={20}>
      {DATA.agents.action_parser.map((p: any, i: number) => {
        const n = DATA.agents.narrative[i];
        const chk = n ? n.check : null;
        return (
          <Stack gap={10} key={i}>
            <H2>行动 #{i + 1}</H2>
            <Callout tone="neutral" title="玩家输入">{p.input.player_action}</Callout>

            <Grid columns="1fr 1fr" gap={14} align="start">
              <Card>
                <CardHeader>ActionParser 输出</CardHeader>
                <CardBody><Stack gap={8}>
                  <Row gap={6} wrap>
                    <Pill size="sm" active>{p.output.action_type}</Pill>
                    <Pill size="sm">{p.output.check_type}</Pill>
                    <Pill size="sm">DC {p.output.suggested_dc}</Pill>
                    <Pill size="sm">{p.output.needs_check ? "需检定" : "无需检定"}</Pill>
                  </Row>
                  <KV k="属性/技能" v={(p.output.attribute_used || "-") + " / " + (p.output.skill_key || "-")} />
                  <KV k="意图" v={p.output.intent || p.output.target} />
                  <KV k="理由" v={p.output.reason} />
                </Stack></CardBody>
              </Card>
              <Card>
                <CardHeader trailing={chk
                  ? <Pill size="sm" active={chk.is_success}>{chk.is_success ? "成功" : "失败"}</Pill>
                  : undefined}>Rule 判定（后端骰点）</CardHeader>
                <CardBody>
                  {chk ? <Stack gap={8}>
                    <KV k="检定" v={chk.check_type + " · " + (chk.attribute_used || "")} />
                    <KV k="掷骰" v={"d20(" + chk.dice_roll + ") + 调整(" + chk.ability_modifier +
                      ") + 熟练(" + chk.skill_bonus + ") = " + chk.final_value} />
                    <KV k="DC" v={String(chk.dc)} />
                    <Text size="small" tone="secondary">{chk.result_text}</Text>
                  </Stack> : <Text size="small" tone="tertiary">本回合无需检定</Text>}
                </CardBody>
              </Card>
            </Grid>

            {n ? (
              <Card>
                <CardHeader trailing={<Pill size="sm" active={n.ai_review.approved}>
                  Critic {n.ai_review.overall_score}</Pill>}>Narrative 输出 + Critic 审核</CardHeader>
                <CardBody><Stack gap={12}>
                  <Mono text={n.story.narration} max={220} />
                  <KV k="visible_result" v={n.story.visible_result} />
                  <KV k="新线索" v={<Chips items={(n.story.new_clues || []).map((c: any) => c.title)} />} />
                  <KV k="后续选项" v={<Chips items={n.story.next_options} />} />
                  <Grid columns="1fr 1fr" gap={14} align="start">
                    <ScoreTable scores={n.ai_review.scores} />
                    <Stack gap={6}>
                      <KV k="approved" v={String(n.ai_review.approved)} />
                      <KV k="revision_count" v={String(n.ai_review.revision_count)} />
                      <KV k="used_fallback" v={String(n.ai_review.used_fallback)} />
                      <KV k="tokens / 延迟" v={n.meta.tokens_used + " / " + n.meta.latency_ms + "ms"} />
                      <KV k="上下文·隐藏真相" v={n.narrative_input_context.hidden_truths_count + " 条（主 Agent 仅见摘要）"} />
                    </Stack>
                  </Grid>
                </Stack></CardBody>
              </Card>
            ) : null}
          </Stack>
        );
      })}
    </Stack>
  );
}

function SummaryView() {
  const s = DATA.agents.summary;
  return (
    <Stack gap={16}>
      <IOColumns
        leftTitle="输入（全局聚合）"
        left={<>
          <KV k="角色" v={s.input.character.name + " · " + s.input.character.profession} />
          <KV k="玩家行动" v={<Chips items={s.input.player_actions} />} />
          <KV k="检定" v={(s.input.check_results || []).map((c: any) =>
            c.check_type + (c.success ? "✓" : "✗")).join("  ")} />
          <KV k="发现线索" v={<Chips items={s.input.discovered_clues} />} />
        </>}
        rightTitle="输出（ReportDTO）"
        right={<>
          <KV k="title" v={<Text size="small" weight="semibold">{s.output.title}</Text>} />
          <KV k="ending_type" v={<Pill size="sm">{s.output.ending_type}</Pill>} />
          <KV k="tokens / 延迟" v={s.tokens_used + " / " + s.latency_ms + "ms"} />
        </>}
      />
      <Card>
        <CardHeader>story_summary</CardHeader>
        <CardBody><Mono text={s.output.story_summary} max={220} /></CardBody>
      </Card>
      <Grid columns="1fr 1fr" gap={14} align="start">
        <Card><CardHeader>关键抉择 key_choices</CardHeader>
          <CardBody><Stack gap={4}>
            {(s.output.key_choices || []).map((c: string, i: number) =>
              <Text key={i} size="small">· {c}</Text>)}
          </Stack></CardBody></Card>
        <Card><CardHeader>角色成长 / 建议</CardHeader>
          <CardBody><Stack gap={8}>
            <Text size="small">{s.output.character_growth}</Text>
            <Divider />
            <Text size="small" tone="secondary">{s.output.next_suggestion}</Text>
          </Stack></CardBody></Card>
      </Grid>
    </Stack>
  );
}

export default function AkpFlowReview() {
  const [tab, setTab] = useCanvasState<string>("tab", "overview");
  const m = DATA.meta;
  return (
    <Stack gap={16} style={{ padding: 24, maxWidth: 1100 }}>
      <Stack gap={4}>
        <H1>AKP 全流程 · Agent 输入输出核验</H1>
        <Text size="small" tone="tertiary">
          模型 {m.model} · AKP 预设 {m.akp_bundle_preset} · {m.generated_at} ·
          规则书 {m.rulebook_file} · 模组 {m.module_file}
        </Text>
      </Stack>

      <Row gap={8} wrap>
        {TABS.map((x) => (
          <Pill key={x.id} active={tab === x.id} onClick={() => setTab(x.id)}>{x.label}</Pill>
        ))}
      </Row>

      <Divider />

      {tab === "overview" ? <Overview /> : null}
      {tab === "akp" ? <AkpView /> : null}
      {tab === "extract" ? <ExtractView /> : null}
      {tab === "opening" ? <OpeningView /> : null}
      {tab === "action" ? <ActionView /> : null}
      {tab === "summary" ? <SummaryView /> : null}
    </Stack>
  );
}
'''


def main() -> None:
    data = json.loads(DUMP.read_text(encoding="utf-8"))
    for pack in data.get("akp", {}).values():
        for b in pack.get("bundles", []):
            md = b.get("bundle_md", "")
            if len(md) > 4200:
                b["bundle_md"] = md[:4200] + "\n… (truncated)"
    literal = json.dumps(data, ensure_ascii=False)
    literal = literal.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    out = TEMPLATE.replace("/*__DATA__*/ null", literal)
    CANVAS.parent.mkdir(parents=True, exist_ok=True)
    CANVAS.write_text(out, encoding="utf-8")
    print(f"[OK] wrote {CANVAS} ({len(out) // 1024} KB)")


if __name__ == "__main__":
    main()
