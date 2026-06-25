"""yishuship PM 评分函数 — 用于 SkillOpt 训练循环和人工质检。

每个函数接收 PM 阶段的 Markdown 输出，返回 0-3 分。
优先用正则/结构检测，只在必要时用 LLM judge。
"""
from __future__ import annotations
import re


# ── 工具函数 ──────────────────────────────────────

def _count_pattern(text: str, pattern: str) -> int:
    """统计模式出现次数。"""
    return len(re.findall(pattern, text, re.IGNORECASE))


def _has_section(text: str, *headers: str) -> bool:
    """检查必需章节是否存在且非空。"""
    for h in headers:
        match = re.search(rf'#+\s*{re.escape(h)}.*?\n(.+?)(?=\n#|\Z)', text, re.DOTALL | re.IGNORECASE)
        if match and match.group(1).strip():
            return True
    return False


def _count_list_items(text: str, section_pattern: str) -> int:
    """统计某个章节下的列表项数。"""
    section = re.search(rf'{section_pattern}.*?\n((?:[-*]\s+.+\n?)+)', text, re.DOTALL | re.IGNORECASE)
    if not section:
        return 0
    return len(re.findall(r'^[-*]\s+', section.group(1), re.MULTILINE))


def _count_table_rows(text: str, header_pattern: str) -> int:
    """统计表格数据行数（不含表头和分隔线）。"""
    lines = text.split('\n')
    in_table = False
    count = 0
    for line in lines:
        stripped = line.strip()
        if not in_table:
            if re.search(header_pattern, stripped, re.IGNORECASE) and stripped.startswith('|'):
                in_table = True
        else:
            if stripped.startswith('|'):
                if '---' not in stripped:
                    count += 1
            else:
                break
    return count


# ── 阶段 1：发现（Discover）──────────────────────

def score_user_persona(text: str) -> float:
    """用户画像具体性：0=无 1=有角色 2=有场景 3=角色+场景+技术水平。"""
    has_role = bool(re.search(r'角色|用户类型|目标用户|persona', text, re.I))
    has_scenario = bool(re.search(r'场景|情境|使用情况|workflow', text, re.I))
    has_tech = bool(re.search(r'技术.*水平|熟练度|新手|专家|skill', text, re.I))
    return float(has_role + has_scenario + has_tech)


def score_existing_solution(text: str) -> float:
    """现有方案描述：0=无 1=提到 2=有描述 3=有具体工具名。"""
    if not re.search(r'现有方案|当前方案|目前.*解决|alternative|现在.*解决|现有.*方式|现状|聊天式|手动', text, re.I):
        return 0.0
    has_desc = bool(re.search(r'通过.*方式|使用.*方法|流程.*是|方式|做法|方案', text, re.I))
    has_tool = bool(re.search(r'[A-Z][a-zA-Z]+\s*(API|SDK|Tool|平台|工具)|https?://|[a-z]+\.(com|cn|io|dev)', text))
    return 1.0 + float(has_desc) + float(has_tool)


def score_problem_evidence(text: str) -> float:
    """问题证据：0=无 1=主观 2=一个来源 3=2+来源。"""
    sources = _count_pattern(text, r'https?://|[a-z]+\.(com|cn|io|dev|org)|根据.*数据|用户.*反馈|调研.*显示|报告.*指出|来源[:：]|\(来源|调查显示|数据.*显示')
    if sources >= 2: return 3.0
    if sources >= 1: return 2.0
    if re.search(r'我觉得|应该|可能|也许', text, re.I): return 1.0
    return 0.0


def score_competitor_count(text: str) -> float:
    """竞品数量：0=0 1=1 2=2 3=3+。"""
    count = _count_table_rows(text, r'竞品|竞争对手|alternative')
    if count >= 3: return 3.0
    if count >= 2: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_competitor_depth(text: str) -> float:
    """竞品分析深度：0=无 1=列名称 2=有方案 3=方案+优劣+评价。"""
    table = re.search(r'^\|.*?竞品.*?$\n(\|.*?$\n)+', text, re.MULTILINE | re.IGNORECASE)
    if not table:
        return 0.0
    header = table.group().split('\n')[0].lower()
    cols = header.count('|') - 1
    if cols >= 4: return 3.0  # 方案+优势+劣势+评价
    if cols >= 3: return 2.0  # 方案+优势+劣势
    if cols >= 1: return 1.0
    return 0.0


def score_opportunity_judgment(text: str) -> float:
    """机会判断：0=无 1=判断无理由 2=有理由 3=理由+证据+不做代价。"""
    has_judgment = bool(re.search(r'值得做|不值得做|建议做|建议不做', text, re.I))
    has_reason = bool(re.search(r'因为|由于|理由|原因', text, re.I))
    has_cost = bool(re.search(r'不做.*代价|不做的.*成本|维持现状', text, re.I))
    return float(has_judgment) + float(has_reason) + float(has_cost)


def score_unique_advantage(text: str) -> float:
    """独特优势：0=无 1=提到 2=有描述 3=优势+竞品对比。"""
    has_we = bool(re.search(r'我们.*优势|我们的.*独特|差异化', text, re.I))
    has_desc = bool(re.search(r'优势.*是|独特.*在于', text, re.I))
    has_compare = bool(re.search(r'相比.*竞品|不同于.*对手|而竞品', text, re.I))
    return float(has_we) + float(has_desc) + float(has_compare)


def score_frequency_severity(text: str) -> float:
    """频率/严重度：0=无 1=提到一个 2=两个都有 3=有量化。"""
    has_freq = bool(re.search(r'每天|每周|每月|频繁|偶尔|罕见|frequency', text, re.I))
    has_severity = bool(re.search(r'阻塞|影响效率|可忍受|严重|轻微|critical|severity', text, re.I))
    has_quantify = bool(re.search(r'\d+%|\d+次|\d+人|N次', text))
    return float(has_freq) + float(has_severity) + float(has_quantify)


def score_discovery_completeness(text: str) -> float:
    """文档完整性：检查必需章节。"""
    required = ['用户画像', '问题验证', '竞品', '机会判断']
    found = sum(1 for r in required if _has_section(text, r))
    if found >= 4: return 3.0
    if found >= 3: return 2.0
    if found >= 1: return 1.0
    return 0.0


# ── 阶段 2：定义（Define）─────────────────────────

def score_positioning(text: str) -> float:
    """一句话定位：0=无 1=太长 2=30-50字 3=≤30字且清晰。"""
    match = re.search(r'一句话[：:]\s*(.+)', text)
    if not match:
        return 0.0
    desc = match.group(1).strip()
    length = len(desc)
    has_structure = bool(re.search(r'为.*解决|帮助.*实现|让.*能够', desc, re.I))
    if length <= 30 and has_structure: return 3.0
    if length <= 50: return 2.0
    return 1.0


def score_differentiation(text: str) -> float:
    """差异化：0=无 1=泛泛 2=1个区别 3=2+具体区别。"""
    diffs = _count_pattern(text, r'区别|不同|独特|差异|vs|versus|而.*不是')
    if diffs >= 3: return 3.0
    if diffs >= 2: return 2.0
    if diffs >= 1: return 1.0
    return 0.0


def score_nongoals(text: str) -> float:
    """Non-goals：0=无 1=1条 2=2-3条 3=4+条。"""
    count = _count_list_items(text, r'不做|non.?goal|边界')
    if count >= 4: return 3.0
    if count >= 2: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_golden_journey_count(text: str) -> float:
    """Golden Journey 数量：0=0 1=1-2 2=3 3=4-5。"""
    count = _count_pattern(text, r'Journey\s*\d|旅程\s*\d|用户路径\s*\d')
    if count >= 4: return 3.0
    if count >= 3: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_journey_completeness(text: str) -> float:
    """Journey 完整性：0=无步骤 1=只有步骤 2=步骤+结果 3=步骤+结果+异常。"""
    has_step = bool(re.search(r'步骤|Step|操作', text, re.I))
    has_result = bool(re.search(r'结果|产出|预期|效果', text, re.I))
    has_error = bool(re.search(r'异常|错误|失败|fallback|兜底', text, re.I))
    return float(has_step) + float(has_result) + float(has_error)


def score_journey_priority(text: str) -> float:
    """Journey 优先级：0=无 1=有无排序 2=P0/P1/P2 3=P0标记不做好不成立。"""
    has_priority = bool(re.search(r'P[012]|优先级|priority', text, re.I))
    has_p0 = bool(re.search(r'P0', text))
    has_critical = bool(re.search(r'不做好.*不成立|必须.*否则|核心.*路径', text, re.I))
    if has_p0 and has_critical: return 3.0
    if has_p0: return 2.0
    if has_priority: return 1.0
    return 0.0


def score_north_star(text: str) -> float:
    """北极星指标：0=无 1=有不可量化 2=可量化无基线 3=可量化+基线+目标。"""
    has_metric = bool(re.search(r'北极星|North Star|核心指标|关键指标', text, re.I))
    has_number = bool(re.search(r'\d+', text))
    has_baseline = bool(re.search(r'基线|当前值|baseline|现状', text, re.I))
    has_target = bool(re.search(r'目标|target|做到.*算成功', text, re.I))
    if has_metric and has_number and has_baseline and has_target: return 3.0
    if has_metric and has_number: return 2.0
    if has_metric: return 1.0
    return 0.0


def score_auxiliary_metrics(text: str) -> float:
    """辅助指标：0=0 1=1个 2=2个 3=3+个。"""
    count = _count_table_rows(text, r'指标|metric|辅助')
    if count >= 3: return 3.0
    if count >= 2: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_appetite(text: str) -> float:
    """范围封顶：0=无 1=有时间无取舍 2=必须做+可以砍 3=有底线。"""
    has_time = bool(re.search(r'时间预算|appetite|最多.*投入|时间.*上限', text, re.I))
    has_must = bool(re.search(r'必须做|must.?have|核心功能', text, re.I))
    has_cut = bool(re.search(r'可以砍|nice.?to.?have|可选功能|时间不够.*砍', text, re.I))
    has_bottom = bool(re.search(r'底线|砍到这里|不是这个产品|minimum viable', text, re.I))
    if has_must and has_cut and has_bottom: return 3.0
    if has_must and has_cut: return 2.0
    if has_time: return 1.0
    return 0.0


def score_define_completeness(text: str) -> float:
    """文档完整性。"""
    required = ['定位', '旅程', '指标', '范围']
    found = sum(1 for r in required if _has_section(text, r))
    if found >= 4: return 3.0
    if found >= 3: return 2.0
    if found >= 1: return 1.0
    return 0.0


# ── 阶段 3：设计（Design）─────────────────────────

def score_info_architecture(text: str) -> float:
    """信息架构：0=无 1=页面列表 2=页面+组件 3=页面+组件+交互流。"""
    has_page = bool(re.search(r'页面|page|screen|视图', text, re.I))
    has_component = bool(re.search(r'组件|component|widget|模块', text, re.I))
    has_flow = bool(re.search(r'交互流|操作流|workflow|用户流', text, re.I))
    return float(has_page) + float(has_component) + float(has_flow)


def score_empty_state(text: str) -> float:
    """空状态设计：0=无 1=提到 2=有描述 3=空状态+引导操作。"""
    has_empty = bool(re.search(r'空状态|empty.*state|无数据|暂无', text, re.I))
    has_guide = bool(re.search(r'引导|提示|CTA|操作按钮', text, re.I))
    has_detail = bool(re.search(r'显示.*文案|展示.*图标|引导.*用户', text, re.I))
    if has_empty and has_guide and has_detail: return 3.0
    if has_empty and has_guide: return 2.0
    if has_empty: return 1.0
    return 0.0


def score_error_state(text: str) -> float:
    """错误状态设计：0=无 1=提到 2=有类型 3=类型+提示+恢复。"""
    has_error = bool(re.search(r'错误|error|失败|异常', text, re.I))
    has_type = bool(re.search(r'网络错误|超时|401|403|500|权限', text, re.I))
    has_recovery = bool(re.search(r'重试|恢复|fallback|降级|提示用户', text, re.I))
    return float(has_error) + float(has_type) + float(has_recovery)


def score_loading_state(text: str) -> float:
    """加载状态设计：0=无 1=提到 2=有描述 3=加载+超时+失败。"""
    has_loading = bool(re.search(r'加载|loading|spinner|骨架', text, re.I))
    has_timeout = bool(re.search(r'超时|timeout|长时间', text, re.I))
    has_fail = bool(re.search(r'加载失败|加载出错', text, re.I))
    return float(has_loading) + float(has_timeout) + float(has_fail)


def score_tech_decision(text: str) -> float:
    """技术选型理由：0=无 1=选型无理由 2=有理由 3=理由+对比+trade-off。"""
    has_choice = bool(re.search(r'选择|选用|采用|选型', text, re.I))
    has_reason = bool(re.search(r'因为|理由|原因|优势在于', text, re.I))
    has_tradeoff = bool(re.search(r'trade.?off|取舍|代价|缺点|但是', text, re.I))
    return float(has_choice) + float(has_reason) + float(has_tradeoff)


def score_data_model(text: str) -> float:
    """数据模型：0=无 1=字段列表 2=字段+类型 3=字段+类型+关系。"""
    has_field = bool(re.search(r'字段|field|column|属性', text, re.I))
    has_type = bool(re.search(r'str|int|float|bool|TEXT|INTEGER|VARCHAR', text, re.I))
    has_relation = bool(re.search(r'外键|关联|关系|foreign|reference|has_many|belongs_to', text, re.I))
    return float(has_field) + float(has_type) + float(has_relation)


def score_api_design(text: str) -> float:
    """API 设计：0=无 1=端点列表 2=端点+请求/响应 3=端点+请求/响应+错误码。"""
    has_endpoint = bool(re.search(r'GET|POST|PUT|DELETE|PATCH|/api/', text))
    has_body = bool(re.search(r'请求体|request.*body|参数|payload', text, re.I))
    has_error = bool(re.search(r'错误码|status.*code|4\d\d|5\d\d|HTTPException', text, re.I))
    return float(has_endpoint) + float(has_body) + float(has_error)


def score_acceptance_count(text: str) -> float:
    """验收标准数量：0=0 1=1-2 2=3-5 3=6+。"""
    count = _count_pattern(text, r'Given.*When.*Then|验收标准|AC\s*\d|验收条件')
    if count >= 6: return 3.0
    if count >= 3: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_acceptance_executable(text: str) -> float:
    """验收标准可执行性：0=无 1=模糊 2=具体 3=Given/When/Then。"""
    has_gwt = bool(re.search(r'Given.*When.*Then', text, re.DOTALL | re.I))
    has_specific = bool(re.search(r'当.*时.*应该|如果.*则.*返回', text, re.I))
    if has_gwt: return 3.0
    if has_specific: return 2.0
    if re.search(r'验收|检查|验证', text, re.I): return 1.0
    return 0.0


def score_risk_assessment(text: str) -> float:
    """风险评估：0=无 1=有风险无缓解 2=风险+缓解 3=风险+缓解+Plan B。"""
    has_risk = bool(re.search(r'风险|risk|不确定性|可能.*失败', text, re.I))
    has_mitigate = bool(re.search(r'缓解|mitigation|应对|预防', text, re.I))
    has_plan_b = bool(re.search(r'Plan\s*B|备选|替代方案|降级方案', text, re.I))
    return float(has_risk) + float(has_mitigate) + float(has_plan_b)


def score_design_completeness(text: str) -> float:
    """文档完整性。"""
    required = ['交互', '技术', '验收', '风险']
    found = sum(1 for r in required if _has_section(text, r))
    if found >= 4: return 3.0
    if found >= 3: return 2.0
    if found >= 1: return 1.0
    return 0.0


# ── 阶段 4：验证（Validate）────────────────────────

def score_hypothesis_identify(text: str) -> float:
    """假设识别：0=无 1=有假设无分类 2=分类 3=分类+验证方法。"""
    has_hypo = bool(re.search(r'假设|hypothesis|前提|前提条件', text, re.I))
    has_class = bool(re.search(r'技术.*假设|产品.*假设|市场.*假设|风险.*假设', text, re.I))
    has_method = bool(re.search(r'验证.*方法|如何.*验证|验证.*方式|测试.*假设', text, re.I))
    return float(has_hypo) + float(has_class) + float(has_method)


def score_plan_review(text: str) -> float:
    """方案评审：0=无 1=自评 2=有评审 3=评审+问题+修复。"""
    has_review = bool(re.search(r'评审|review|审查|检查', text, re.I))
    has_issue = bool(re.search(r'问题|issue|发现|concern|风险点', text, re.I))
    has_fix = bool(re.search(r'修复|修改|调整|改进|解决', text, re.I))
    return float(has_review) + float(has_issue) + float(has_fix)


def score_minimal_validation(text: str) -> float:
    """最小验证方案：0=无 1=有不可执行 2=可执行 3=可执行+预期+判断标准。"""
    has_plan = bool(re.search(r'验证.*方案|最小.*验证|MVP|原型|mock', text, re.I))
    has_step = bool(re.search(r'步骤|Step|操作|执行', text, re.I))
    has_criteria = bool(re.search(r'如果.*则|预期.*结果|判断.*标准|通过.*条件', text, re.I))
    return float(has_plan) + float(has_step) + float(has_criteria)


def score_scope_consistency(text: str) -> float:
    """范围一致性：与定义阶段对比，无未标记新增。"""
    has_new = bool(re.search(r'新增|添加|追加|补充', text, re.I))
    has_marked = bool(re.search(r'新增.*已标记|标记.*新增|范围.*变更', text, re.I))
    has_diff = bool(re.search(r'与.*定义.*一致|范围.*未变|无.*新增', text, re.I))
    if has_diff: return 3.0
    if has_new and has_marked: return 2.0
    if has_new: return 1.0
    return 2.0  # 无新增默认合格


def score_hypothesis_status(text: str) -> float:
    """核心假设状态：0=无 1=有假设无状态 2=标记状态 3=已验证+证据。"""
    has_hypo = bool(re.search(r'假设|hypothesis', text, re.I))
    has_status = bool(re.search(r'已验证|未验证|已确认|待确认|passed|failed', text, re.I))
    has_evidence = bool(re.search(r'证据|evidence|数据.*支持|测试.*结果', text, re.I))
    if has_hypo and has_status and has_evidence: return 3.0
    if has_hypo and has_status: return 2.0
    if has_hypo: return 1.0
    return 0.0


def score_validate_completeness(text: str) -> float:
    """文档完整性。"""
    required = ['假设', '评审', '验证']
    found = sum(1 for r in required if _has_section(text, r))
    if found >= 3: return 3.0
    if found >= 2: return 2.0
    if found >= 1: return 1.0
    return 0.0


# ── 阶段 5：实现（Build）──────────────────────────

def score_scope_guard(text: str) -> float:
    """范围守护：0=膨胀 1=有膨胀标记了 2=无膨胀 3=无膨胀+主动砍。"""
    has_bloat = bool(re.search(r'范围.*膨胀|新增.*功能|超出.*范围|scope.*creep', text, re.I))
    has_cut = bool(re.search(r'砍掉|移除|推迟|不做', text, re.I))
    has_clean = bool(re.search(r'范围.*一致|无.*膨胀|严格.*范围', text, re.I))
    if has_clean and has_cut: return 3.0
    if has_clean: return 2.0
    if has_bloat: return 1.0
    return 2.0  # 无膨胀信号默认合格


def score_acceptance_pass_rate(text: str) -> float:
    """验收标准通过率：0=0% 1=<60% 2=60-90% 3=100%。"""
    total = _count_pattern(text, r'验收标准|AC\s*\d|Given.*When.*Then')
    passed = _count_pattern(text, r'✅|通过|passed|PASS')
    if total == 0:
        return 1.0  # 有验收但未统计
    rate = passed / total if total > 0 else 0
    if rate >= 1.0: return 3.0
    if rate >= 0.6: return 2.0
    if rate > 0: return 1.0
    return 0.0


def test_coverage(text: str) -> float:
    """测试覆盖：0=无 1=部分 2=核心路径 3=核心+边界+异常。"""
    has_test = bool(re.search(r'测试|test|pytest|jest|vitest', text, re.I))
    has_core = bool(re.search(r'核心.*路径|主.*流程|happy.*path', text, re.I))
    has_edge = bool(re.search(r'边界|edge.*case|异常.*路径|错误.*路径', text, re.I))
    if has_test and has_core and has_edge: return 3.0
    if has_test and has_core: return 2.0
    if has_test: return 1.0
    return 0.0


def score_code_quality(text: str) -> float:
    """代码质量：0=安全漏洞 1=lint错误 2=lint通过 3=lint+无死代码。"""
    has_security = bool(re.search(r'安全.*漏洞|vulnerability|XSS|SQL.*注入|pickle', text, re.I))
    has_lint_error = bool(re.search(r'lint.*错误|lint.*失败|type.*error', text, re.I))
    has_lint_pass = bool(re.search(r'lint.*通过|无.*警告|clean.*code', text, re.I))
    has_no_dead = bool(re.search(r'无.*死代码|无.*未使用|no.*unused', text, re.I))
    if has_security: return 0.0
    if has_lint_pass and has_no_dead: return 3.0
    if has_lint_pass: return 2.0
    if has_lint_error: return 1.0
    return 2.0  # 无负面信号默认合格


def score_commit规范(text: str) -> float:
    """提交规范：0=无 1=有无消息 2=规范消息 3=规范+关联issue。"""
    has_commit = bool(re.search(r'commit|提交|git', text, re.I))
    has规范 = bool(re.search(r'feat|fix|refactor|docs|test|chore|conventional', text, re.I))
    has_issue = bool(re.search(r'#\d+|issue|ticket|关联.*需求', text, re.I))
    if has_commit and has规范 and has_issue: return 3.0
    if has_commit and has规范: return 2.0
    if has_commit: return 1.0
    return 0.0


def score_doc_update(text: str) -> float:
    """文档更新：0=无 1=README 2=README+API 3=README+API+CHANGELOG。"""
    has_readme = bool(re.search(r'README|项目说明', text, re.I))
    has_api = bool(re.search(r'API.*文档|接口.*文档|swagger|openapi', text, re.I))
    has_changelog = bool(re.search(r'CHANGELOG|变更.*日志|release.*note', text, re.I))
    return float(has_readme) + float(has_api) + float(has_changelog)


def score_build_status(text: str) -> float:
    """构建状态：0=失败 1=警告 2=通过 3=通过+测试通过。"""
    has_fail = bool(re.search(r'构建.*失败|build.*fail|编译.*错误', text, re.I))
    has_warn = bool(re.search(r'警告|warning|deprecated', text, re.I))
    has_pass = bool(re.search(r'构建.*通过|build.*pass|编译.*成功', text, re.I))
    has_test_pass = bool(re.search(r'测试.*通过|test.*pass|all.*green', text, re.I))
    if has_fail: return 0.0
    if has_pass and has_test_pass: return 3.0
    if has_pass: return 2.0
    if has_warn: return 1.0
    return 2.0


def score_dev_context(text: str) -> float:
    """实现上下文：0=无 1=有不完整 2=完整 3=完整+模式引用。"""
    has_context = bool(re.search(r'实现.*上下文|dev.*context|实现.*记录', text, re.I))
    has_pattern = bool(re.search(r'模式|pattern|参考.*实现|类似.*功能', text, re.I))
    has完整 = bool(re.search(r'入口.*文件|调用.*链|数据.*流', text, re.I))
    if has_context and has_pattern and has完整: return 3.0
    if has_context and has完整: return 2.0
    if has_context: return 1.0
    return 0.0


# ── 阶段 6：发布（Release）────────────────────────

def score_journey验收(text: str) -> float:
    """Golden Journey 验收：0=0条 1=部分 2=全部 3=全部+边界。"""
    total = _count_pattern(text, r'Journey.*验收|旅程.*验收|用户路径.*验证')
    passed = _count_pattern(text, r'✅|通过|passed')
    if total == 0:
        return 0.0
    if passed >= total:
        has_edge = bool(re.search(r'边界.*测试|edge.*case|异常.*路径', text, re.I))
        return 3.0 if has_edge else 2.0
    if passed > 0: return 1.0
    return 0.0


def score_e2e_status(text: str) -> float:
    """E2E 测试：0=无 1=有失败 2=通过 3=通过+无flaky。"""
    has_e2e = bool(re.search(r'E2E|end.*to.*end|端到端|e2e', text, re.I))
    has_fail = bool(re.search(r'E2E.*失败|e2e.*fail', text, re.I))
    has_pass = bool(re.search(r'E2E.*通过|e2e.*pass|E2E.*green', text, re.I))
    has_flaky = bool(re.search(r'flaky|不稳定|intermittent', text, re.I))
    if has_fail: return 1.0
    if has_pass and not has_flaky: return 3.0
    if has_pass: return 2.0
    if has_e2e: return 1.0
    return 0.0


def score_release_checklist(text: str) -> float:
    """发布清单：0=无 1=有不全 2=完整 3=完整+逐项打勾。"""
    has_list = bool(re.search(r'发布.*清单|release.*checklist|发布.*检查', text, re.I))
    has_items = _count_list_items(text, r'清单|checklist|检查')
    has_check = _count_pattern(text, r'\[[xX]\]|✅|已完成|done')
    if has_list and has_check >= 3: return 3.0
    if has_list and has_items >= 3: return 2.0
    if has_list: return 1.0
    return 0.0


def score_rollback_plan(text: str) -> float:
    """回滚方案：0=无 1=有不可执行 2=可执行 3=可执行+已验证。"""
    has_plan = bool(re.search(r'回滚|rollback|回退|还原', text, re.I))
    has_cmd = bool(re.search(r'git.*revert|git.*reset|docker.*rollback|部署.*回退', text, re.I))
    has验证 = bool(re.search(r'已验证|已测试|回滚.*成功|验证.*回滚', text, re.I))
    if has_plan and has_cmd and has验证: return 3.0
    if has_plan and has_cmd: return 2.0
    if has_plan: return 1.0
    return 0.0


def score_monitoring_plan(text: str) -> float:
    """监控方案：0=无 1=指标列表 2=指标+阈值 3=指标+阈值+告警。"""
    has_metric = bool(re.search(r'监控.*指标|metric|指标.*列表|关键.*指标', text, re.I))
    has_threshold = bool(re.search(r'阈值|threshold|上限|下限|告警.*线', text, re.I))
    has_alert = bool(re.search(r'告警|alert|通知|触发.*告警|P0.*告警', text, re.I))
    return float(has_metric) + float(has_threshold) + float(has_alert)


def score_pr_ci_status(text: str) -> float:
    """PR/CI 状态：0=无 1=PR创建 2=CI通过 3=CI+review通过。"""
    has_pr = bool(re.search(r'PR|pull.*request|合并.*请求', text, re.I))
    has_ci = bool(re.search(r'CI.*通过|CI.*green|checks.*pass|GitHub.*check', text, re.I))
    has_review = bool(re.search(r'review.*通过|approve|LGTM|审核.*通过', text, re.I))
    if has_pr and has_ci and has_review: return 3.0
    if has_pr and has_ci: return 2.0
    if has_pr: return 1.0
    return 0.0


def score_changelog(text: str) -> float:
    """变更日志：0=无 1=有不全 2=完整 3=完整+分类。"""
    has_log = bool(re.search(r'CHANGELOG|变更.*日志|release.*note', text, re.I))
    has分类 = bool(re.search(r'feat|fix|refactor|perf|docs|breaking', text, re.I))
    has_version = bool(re.search(r'v\d+\.\d+|版本.*号|version', text, re.I))
    if has_log and has分类 and has_version: return 3.0
    if has_log and has分类: return 2.0
    if has_log: return 1.0
    return 0.0


# ── 阶段 7：观察（Observe）────────────────────────

def score_north_star追踪(text: str) -> float:
    """北极星追踪：0=无 1=有数据无对比 2=与基线对比 3=对比+趋势。"""
    has_data = bool(re.search(r'北极星|north.*star|核心.*指标.*数据', text, re.I))
    has对比 = bool(re.search(r'基线|baseline|对比|vs|相比', text, re.I))
    has趋势 = bool(re.search(r'上升|下降|持平|趋势|improving|declining|stable', text, re.I))
    return float(has_data) + float(has对比) + float(has趋势)


def score_auxiliary_追踪(text: str) -> float:
    """辅助指标覆盖：0=0个 1=1-2个 2=全部 3=全部+异常。"""
    count = _count_pattern(text, r'指标.*\d|metric.*\d|\d+%|\d+次')
    has异常 = bool(re.search(r'异常.*指标|意外.*信号|负面.*信号', text, re.I))
    if count >= 3 and has异常: return 3.0
    if count >= 3: return 2.0
    if count >= 1: return 1.0
    return 0.0


def score_user_feedback(text: str) -> float:
    """用户反馈：0=无 1=有无分类 2=分类 3=分类+频率。"""
    has_feedback = bool(re.search(r'用户.*反馈|feedback|用户.*评价|用户.*说', text, re.I))
    has分类 = bool(re.search(r'正面|负面|中性|positive|negative|neutral', text, re.I))
    has频率 = bool(re.search(r'频率|出现.*次|占比|%\s*的.*用户', text, re.I))
    return float(has_feedback) + float(has分类) + float(has频率)


def score_problem识别(text: str) -> float:
    """问题识别：0=无 1=有无优先级 2=有优先级 3=优先级+影响范围。"""
    has_problem = bool(re.search(r'问题|bug|issue|故障', text, re.I))
    has_priority = bool(re.search(r'P[012]|优先级|priority|严重|critical', text, re.I))
    has_impact = bool(re.search(r'影响.*范围|影响.*用户|受影响|impact', text, re.I))
    return float(has_problem) + float(has_priority) + float(has_impact)


def score意外发现(text: str) -> float:
    """意外发现：0=无 1=有未分析 2=有分析 3=分析+行动建议。"""
    has发现 = bool(re.search(r'意外|发现|surprising|unexpected|出乎意料', text, re.I))
    has分析 = bool(re.search(r'分析|原因.*是|可能.*因为|这是因为', text, re.I))
    has行动 = bool(re.search(r'行动|建议|改进|优化|下一步', text, re.I))
    return float(has发现) + float(has分析) + float(has行动)


def score_data_credibility(text: str) -> float:
    """数据可信度：0=无数据 1=样本太小 2=样本足够 3=样本+来源。"""
    has_data = bool(re.search(r'\d+%|\d+次|\d+人|数据|data', text, re.I))
    has_sample = bool(re.search(r'样本|sample|N\s*=\s*\d+|用户数', text, re.I))
    has_source = bool(re.search(r'来源|source|数据.*来自|采集.*方式', text, re.I))
    if has_data and has_sample and has_source: return 3.0
    if has_data and has_sample: return 2.0
    if has_data: return 1.0
    return 0.0


# ── 阶段 8：学习（Learn）──────────────────────────

def score假设回顾(text: str) -> float:
    """假设回顾：0=无 1=有无分类 2=分类 3=分类+原因。"""
    has回顾 = bool(re.search(r'假设.*回顾|回顾.*假设|hypothesis.*review', text, re.I))
    has分类 = bool(re.search(r'正确|错误|对了|错了|验证.*通过|验证.*失败', text, re.I))
    has原因 = bool(re.search(r'因为|原因|why|根因', text, re.I))
    return float(has回顾) + float(has分类) + float(has原因)


def score_错因分析(text: str) -> float:
    """错因分析：0=无 1=没想到 2=具体原因 3=原因+认知偏差。"""
    has分析 = bool(re.search(r'为什么.*错|错.*原因|失败.*原因', text, re.I))
    has具体 = bool(re.search(r'因为.*具体|信息.*不足|假设.*错误|市场.*变化', text, re.I))
    has偏差 = bool(re.search(r'认知.*偏差|confirmation.*bias|过度.*乐观|幸存者.*偏差', text, re.I))
    return float(has分析) + float(has具体) + float(has偏差)


def score_决策复盘(text: str) -> float:
    """决策复盘：0=无 1=有无分类 2=好/坏分类 3=分类+如果重来。"""
    has复盘 = bool(re.search(r'决策.*复盘|复盘.*决策|decision.*review', text, re.I))
    has分类 = bool(re.search(r'做得好|做得对|做错了|好的.*决策|坏的.*决策', text, re.I))
    has重来 = bool(re.search(r'如果重来|下次.*会|should.*have|would.*do', text, re.I))
    return float(has复盘) + float(has分类) + float(has重来)


def score_经验沉淀(text: str) -> float:
    """经验沉淀：0=无 1=有未结构化 2=结构化 3=结构化+可复用。"""
    has经验 = bool(re.search(r'教训|经验|lesson|learnings|takeaway', text, re.I))
    has结构 = bool(re.search(r'\d+\.|•|-|规则|原则', text, re.I))
    has复用 = bool(re.search(r'可复用|通用|以后.*遇到|下次.*直接', text, re.I))
    return float(has经验) + float(has结构) + float(has复用)


def score_dec_record(text: str) -> float:
    """DEC-NNNN 记录：0=无 1=有不全 2=完整 3=完整+重新评估。"""
    has_dec = bool(re.search(r'DEC-\d+|决策.*记录|decision.*record', text, re.I))
    has完整 = bool(re.search(r'决策|理由|拒绝.*方案|验收.*证据', text, re.I))
    has评估 = bool(re.search(r'重新.*评估|reconsider|何时.*重新|触发.*条件', text, re.I))
    if has_dec and has完整 and has评估: return 3.0
    if has_dec and has完整: return 2.0
    if has_dec: return 1.0
    return 0.0


def score_next_iteration(text: str) -> float:
    """下一迭代方向：0=无 1=有模糊 2=具体 3=具体+优先级+理由。"""
    has方向 = bool(re.search(r'下一.*迭代|next.*iteration|下一步|接下来', text, re.I))
    has具体 = bool(re.search(r'具体.*方向|重点.*是|首要.*问题|最重要', text, re.I))
    has理由 = bool(re.search(r'因为|理由|基于.*学习|根据.*数据', text, re.I))
    return float(has方向) + float(has具体) + float(has理由)


# ── 汇总 ──────────────────────────────────────────

STAGE_1_SCORERS = [
    score_user_persona, score_existing_solution, score_problem_evidence,
    score_competitor_count, score_competitor_depth, score_opportunity_judgment,
    score_unique_advantage, score_frequency_severity, score_discovery_completeness,
]

STAGE_2_SCORERS = [
    score_positioning, score_differentiation, score_nongoals,
    score_golden_journey_count, score_journey_completeness, score_journey_priority,
    score_north_star, score_auxiliary_metrics, score_appetite, score_define_completeness,
]

STAGE_3_SCORERS = [
    score_info_architecture, score_empty_state, score_error_state, score_loading_state,
    score_tech_decision, score_data_model, score_api_design,
    score_acceptance_count, score_acceptance_executable, score_risk_assessment,
    score_design_completeness,
]

STAGE_4_SCORERS = [
    score_hypothesis_identify, score_plan_review, score_minimal_validation,
    score_scope_consistency, score_hypothesis_status, score_validate_completeness,
]

STAGE_5_SCORERS = [
    score_scope_guard, score_acceptance_pass_rate, test_coverage,
    score_code_quality, score_commit规范, score_doc_update,
    score_build_status, score_dev_context,
]

STAGE_6_SCORERS = [
    score_journey验收, score_e2e_status, score_release_checklist,
    score_rollback_plan, score_monitoring_plan, score_pr_ci_status, score_changelog,
]

STAGE_7_SCORERS = [
    score_north_star追踪, score_auxiliary_追踪, score_user_feedback,
    score_problem识别, score意外发现, score_data_credibility,
]

STAGE_8_SCORERS = [
    score假设回顾, score_错因分析, score_决策复盘,
    score_经验沉淀, score_dec_record, score_next_iteration,
]

ALL_SCORERS = {
    "discover": (STAGE_1_SCORERS, 27, 17),
    "define":   (STAGE_2_SCORERS, 30, 19),
    "design":   (STAGE_3_SCORERS, 33, 21),
    "validate": (STAGE_4_SCORERS, 18, 12),
    "build":    (STAGE_5_SCORERS, 24, 15),
    "release":  (STAGE_6_SCORERS, 21, 14),
    "observe":  (STAGE_7_SCORERS, 18, 12),
    "learn":    (STAGE_8_SCORERS, 18, 12),
}


def score_stage(stage: str, output: str) -> dict:
    """对一个阶段的输出评分。

    Returns:
        {"total": float, "max": float, "pass": float, "passOrFail": bool, "details": {...}}
    """
    scorers, max_score, pass_score = ALL_SCORERS[stage]
    details = {}
    total = 0.0
    for fn in scorers:
        name = fn.__name__
        s = fn(output)
        details[name] = s
        total += s
    return {
        "total": total,
        "max": max_score,
        "pass_threshold": pass_score,
        "passOrFail": total >= pass_score,
        "details": details,
    }


def score_full_pipeline(outputs: dict[str, str]) -> dict:
    """对全流程 8 个阶段评分。

    Args:
        outputs: {"discover": "...", "define": "...", ...}

    Returns:
        {"stages": {...}, "total": float, "max": float, "all_pass": bool}
    """
    results = {}
    total = 0.0
    max_total = 0.0
    all_pass = True
    for stage, (scorers, max_s, pass_s) in ALL_SCORERS.items():
        if stage in outputs:
            r = score_stage(stage, outputs[stage])
            results[stage] = r
            total += r["total"]
            max_total += max_s
            if not r["passOrFail"]:
                all_pass = False
        else:
            results[stage] = {"total": 0, "max": max_s, "pass_threshold": pass_s, "passOrFail": False}
            all_pass = False
            max_total += max_s
    return {
        "stages": results,
        "total": total,
        "max": max_total,
        "all_pass": all_pass,
    }
