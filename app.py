"""
GWS Agent Architecture Sales Dojo v4.0 (Fortified)
===================================================
Powered by Business Ecosystem Grand Architect

Features:
- Self-healing error recovery
- Input sanitization
- State management with fallbacks
- Resilient operation decorators
- Manager Evaluation Panel
"""

import streamlit as st
import random
import time
import logging
import traceback
from enum import Enum
from functools import wraps

# --- 0. Robust Config & Logging ---
st.set_page_config(layout="wide", page_title="GWS Sales Dojo v4.0 (Fortified)")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CSS Styling ---
st.markdown("""
<style>
    .score-high { color: #28a745; font-weight: bold; }
    .score-mid { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .review-box { background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4CAF50; border-radius: 5px; margin: 10px 0; }
    .review-box-warning { background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; border-radius: 5px; margin: 10px 0; }
    .review-box-danger { background-color: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; border-radius: 5px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- Resilient Operation Decorator ---
def resilient_op(func):
    """Decorator for self-healing operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Operation {func.__name__} failed: {e}\n{traceback.format_exc()}")
            st.session_state.error_count = st.session_state.get("error_count", 0) + 1
            return None
    return wrapper


# --- SPIN Stages Definition ---
class SPINStage(Enum):
    OPENING = "Opening (挨拶・ラポール)"
    SITUATION = "Situation (現状把握)"
    PROBLEM = "Problem (課題抽出)"
    IMPLICATION = "Implication (問題の深刻化)"
    NEED_PAYOFF = "Need-payoff (解決の価値・提案)"
    CLOSING = "Closing (合意形成)"


# --- 1. Safe State Management ---
def init_state():
    """Initialize all state variables with safe defaults"""
    defaults = {
        "messages": [],
        "review_log": [],
        "simulation_active": False,
        "customer_persona": {},
        "demo_mode": False,
        "auto_run": False,
        "auto_run_first": True,
        "current_stage": SPINStage.OPENING,
        "error_count": 0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Validate current_stage is valid
    if not isinstance(st.session_state.get("current_stage"), SPINStage):
        st.session_state.current_stage = SPINStage.OPENING


init_state()


def safe_get_persona():
    """Safely get persona with fallback"""
    persona = st.session_state.get("customer_persona", {})
    if not persona or "industry" not in persona:
        return {
            "industry": "製造",
            "position": "部長",
            "personality": "慎重派",
            "budget": "500万円"
        }
    return persona


def sanitize_input(text, max_length=500):
    """Sanitize user input to prevent injection and limit length"""
    if not text or not isinstance(text, str):
        return ""
    # Remove dangerous characters
    clean = text.replace("<", "&lt;").replace(">", "&gt;")
    clean = clean.replace("${", "").replace("{{", "").replace("}}", "")
    # Limit length
    return clean[:max_length].strip()


# --- 2. Logic Engines (Resilient) ---

@resilient_op
def get_demo_sales_response(stage, persona):
    """Safe demo response generation"""
    persona = persona or safe_get_persona()

    responses = {
        SPINStage.OPENING: f"本日はお時間をいただきありがとうございます。{persona.get('industry', '貴社')}業界では最近、人手不足が深刻だと伺いますが、御社の状況はいかがでしょうか？",
        SPINStage.SITUATION: "なるほど。具体的には、請求書の処理業務には現在どのくらいの人数と時間を割かれているのですか？",
        SPINStage.PROBLEM: "それは大きな負担ですね。特に月末の締め処理などで、ミスが発生したり、残業が増えたりする課題はございませんか？",
        SPINStage.IMPLICATION: "もしそのミスが見過ごされた場合、取引先との信頼関係や、修正にかかるコストはどれくらいの影響になるとお考えでしょうか？",
        SPINStage.NEED_PAYOFF: "ありがとうございます。もし、その『確認作業』自体をAIエージェントが代行し、担当者様は『最終承認ボタンを押すだけ』になれば、本来注力すべき業務に時間を割けると思いませんか？",
        SPINStage.CLOSING: f"まずはその請求書処理の部分だけ、300万円未満（{persona.get('budget', '予算内')}の範囲内）のトライアルとして導入し、効果を検証してみませんか？"
    }
    return responses.get(stage, "次のステップについてご相談させてください。")


@resilient_op
def evaluate_turn_logic(user_input, current_stage_enum):
    """Resilient input evaluation with detailed scoring"""
    # Input validation
    if not user_input or not isinstance(user_input, str):
        return {
            "status": "⚠️ Empty Input",
            "comment": "入力が空です。何か提案を入力してください。",
            "score": 0,
            "breakdown": {"spin_flow": 0, "keywords": 0, "strategy": 0, "engagement": 0},
            "improvement": "具体的な提案や質問を入力してください。"
        }, current_stage_enum

    # Sanitize input
    clean_input = sanitize_input(user_input)
    if len(clean_input) < 2:
        return {
            "status": "⚠️ Invalid Input",
            "comment": "有効な入力ではありません。",
            "score": 0,
            "breakdown": {"spin_flow": 0, "keywords": 0, "strategy": 0, "engagement": 0},
            "improvement": "日本語で具体的な提案を入力してください。"
        }, current_stage_enum

    # Validate stage
    if not isinstance(current_stage_enum, SPINStage):
        current_stage_enum = SPINStage.OPENING

    input_text = clean_input.lower()
    detected_stage = SPINStage.SITUATION  # Default

    # Keyword-based stage detection
    if any(w in input_text for w in ["はじめ", "ありがとう", "挨拶", "よろしく"]):
        detected_stage = SPINStage.OPENING
    elif any(w in input_text for w in ["現状", "フロー", "人数", "どのよう", "いかが"]):
        detected_stage = SPINStage.SITUATION
    elif any(w in input_text for w in ["課題", "困っ", "ミス", "問題", "悩み"]):
        detected_stage = SPINStage.PROBLEM
    elif any(w in input_text for w in ["影響", "リスク", "損失", "コスト", "深刻"]):
        detected_stage = SPINStage.IMPLICATION
    elif any(w in input_text for w in ["解決", "提案", "gem", "ai", "エージェント"]):
        detected_stage = SPINStage.NEED_PAYOFF
    elif any(w in input_text for w in ["契約", "金額", "poc", "トライアル", "やる", "導入"]):
        detected_stage = SPINStage.CLOSING

    # Stage transition logic with safe index access
    stage_order = list(SPINStage)
    try:
        current_index = stage_order.index(current_stage_enum)
        detected_index = stage_order.index(detected_stage)
    except ValueError:
        current_index = 0
        detected_index = 0

    # Calculate detailed scores
    breakdown = {"spin_flow": 0, "keywords": 0, "strategy": 0, "engagement": 0}

    # SPIN Flow Score (40 points max)
    if detected_index > current_index + 1:
        feedback_status = "⚠️ Alert: Skipping Stages"
        feedback_comment = f"段階を飛ばしています！現在は「{current_stage_enum.value.split(' ')[0]}」フェーズです。課題の深掘りを優先してください。"
        breakdown["spin_flow"] = 10
        next_stage = current_stage_enum
    elif detected_index < current_index:
        feedback_status = "🔄 Loop Back"
        feedback_comment = "前のフェーズに戻りました。確認は良いですが、話を進展させましょう。"
        breakdown["spin_flow"] = 25
        next_stage = current_stage_enum
    else:
        feedback_status = "✅ Good Progression"
        feedback_comment = f"順調です。{detected_stage.value} の意図が伝わりました。"
        breakdown["spin_flow"] = 40
        next_stage = detected_stage

    # Keywords Score (30 points max)
    good_keywords = ["gem", "エージェント", "承認", "人間", "循環", "連携", "リルート", "自動化"]
    keyword_hits = sum(1 for kw in good_keywords if kw in input_text)
    breakdown["keywords"] = min(keyword_hits * 10, 30)

    # Strategy Score (20 points max)
    strategy_keywords = ["スモールスタート", "トライアル", "poc", "まずは", "300万", "500万", "絞っ"]
    strategy_hits = sum(1 for kw in strategy_keywords if kw in input_text)
    breakdown["strategy"] = min(strategy_hits * 10, 20)

    # Engagement Score (10 points max)
    if len(clean_input) > 100:
        breakdown["engagement"] = 10
    elif len(clean_input) > 50:
        breakdown["engagement"] = 7
    elif len(clean_input) > 20:
        breakdown["engagement"] = 5
    else:
        breakdown["engagement"] = 2

    total_score = sum(breakdown.values())
    improvement = get_improvement_advice(breakdown, total_score)

    return {
        "status": feedback_status,
        "comment": feedback_comment,
        "score": total_score,
        "breakdown": breakdown,
        "improvement": improvement,
        "detected_stage": detected_stage.name,
        "next_stage": next_stage.name
    }, next_stage


def get_improvement_advice(breakdown, total_score):
    """Generate improvement advice based on scores"""
    advice = []
    if breakdown["spin_flow"] < 30:
        advice.append("SPINの順序を守り、段階を飛ばさないようにしましょう。")
    if breakdown["keywords"] < 15:
        advice.append("Gem、承認フロー、連携などの技術キーワードを使いましょう。")
    if breakdown["strategy"] < 10:
        advice.append("スモールスタートやトライアル提案で着地点を示しましょう。")
    if breakdown["engagement"] < 5:
        advice.append("もう少し詳しく説明を加えましょう。")

    if not advice:
        if total_score >= 80:
            return "🏆 素晴らしい提案です！この調子で商談をクロージングに導きましょう。"
        else:
            return "良い提案です。さらに具体的な数字や事例を加えると説得力が増します。"

    return " ".join(advice)


def run_demo_turn():
    """Execute one demo turn with full error handling"""
    try:
        # Validate state
        if not isinstance(st.session_state.current_stage, SPINStage):
            st.session_state.current_stage = SPINStage.OPENING

        persona = safe_get_persona()
        st.session_state.customer_persona = persona

        current_stage = st.session_state.current_stage

        # Generate demo response
        demo_input = get_demo_sales_response(current_stage, persona)
        if not demo_input:
            demo_input = "次のステップについてご相談させてください。"

        # Calculate next stage
        stage_order = list(SPINStage)
        try:
            current_idx = stage_order.index(current_stage)
        except ValueError:
            current_idx = 0

        next_stage = stage_order[min(current_idx + 1, len(stage_order) - 1)]
        st.session_state.current_stage = next_stage

        # Add messages
        st.session_state.messages.append({
            "role": "user",
            "content": demo_input,
            "type": "demo"
        })

        st.session_state.review_log.append({
            "turn": len(st.session_state.messages) // 2,
            "is_human": False,
            "stage": current_stage.value,
            "feedback": {
                "status": "✅ Demo: Ideal Progression",
                "comment": f"トップパフォーマーの{current_stage.value.split(' ')[0]}フェーズ対応",
                "score": 95,
                "breakdown": {"spin_flow": 40, "keywords": 25, "strategy": 20, "engagement": 10},
                "improvement": "模範的なSPIN営業です。"
            }
        })

        # Customer response
        customer_responses = {
            SPINStage.OPENING: f"はい、{persona.get('industry', '当社')}の現場は確かに人手不足です。何かお考えがあるのですか？",
            SPINStage.SITUATION: "そうですね、請求書処理には3名で月に約40時間かけています。",
            SPINStage.PROBLEM: "おっしゃる通り、月末は特に残業が増えますね。ミスも時々発生します。",
            SPINStage.IMPLICATION: "確かに、取引先への謝罪や修正作業で余計なコストがかかっていますね...",
            SPINStage.NEED_PAYOFF: "なるほど、最終承認だけで済むなら魅力的ですね。具体的にはどういう形で始められますか？",
            SPINStage.CLOSING: "その条件なら前向きに検討できそうです。社内で相談してみます。"
        }
        cust_resp = customer_responses.get(current_stage, "なるほど、続けてください。")
        st.session_state.messages.append({
            "role": "assistant",
            "content": cust_resp,
            "type": "ai"
        })

        return True

    except Exception as e:
        logger.error(f"Demo turn failed: {e}")
        st.error(f"デモ実行中にエラーが発生しました。リセットしてやり直してください。")
        return False


# --- 3. UI Components ---

def init_scenario():
    """Initialize a new scenario with safe defaults"""
    st.session_state.messages = []
    st.session_state.review_log = []
    st.session_state.simulation_active = True
    st.session_state.current_stage = SPINStage.OPENING
    st.session_state.auto_run = False
    st.session_state.auto_run_first = True
    st.session_state.error_count = 0

    if not st.session_state.get("customer_persona") or not st.session_state.customer_persona.get("industry"):
        st.session_state.customer_persona = {
            "industry": random.choice(["物流", "金融", "製造", "ヘルスケア", "SaaS"]),
            "position": random.choice(["業務改革部長", "DX推進室長", "事業部長", "課長"]),
            "personality": random.choice(["慎重派。コスト意識が高い。", "革新的だが実績を重視。", "現場からの反発を懸念。"]),
            "budget": random.choice(["300万円", "500万円", "1000万円"])
        }

    p = st.session_state.customer_persona
    msg = f"（{p.get('industry', '企業')}業界 / {p.get('position', '担当者')}）\nはい、どういったご用件でしょうか？ {p.get('personality', '')} なので、手短にお願いします。"
    st.session_state.messages.append({"role": "assistant", "content": msg, "type": "ai"})


# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ GWS Dojo v4.0")
    st.caption("Fortified Edition")

    with st.expander("👤 ペルソナ設定", expanded=True):
        curr_p = st.session_state.get("customer_persona", {}) or {}
        p_industry = st.text_input("業界", value=curr_p.get("industry", "製造"))
        p_position = st.text_input("役職", value=curr_p.get("position", "部長"))
        p_personality = st.text_input("性格", value=curr_p.get("personality", "慎重派"))
        p_budget = st.text_input("予算", value=curr_p.get("budget", "500万円"))

        if st.button("✅ 設定を反映"):
            st.session_state.customer_persona = {
                "industry": sanitize_input(p_industry, 50),
                "position": sanitize_input(p_position, 50),
                "personality": sanitize_input(p_personality, 100),
                "budget": sanitize_input(p_budget, 50)
            }
            init_scenario()
            st.rerun()

    st.markdown("---")

    if st.button("🆕 新規シナリオ開始", type="primary"):
        st.session_state.customer_persona = {}
        init_scenario()
        st.rerun()

    if st.session_state.simulation_active:
        persona = safe_get_persona()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <strong>🎯 Target:</strong><br>
            {persona.get('industry', 'N/A')} / {persona.get('position', 'N/A')}<br>
            <small>予算: {persona.get('budget', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        is_demo = st.toggle("🤖 デモモード", value=st.session_state.demo_mode)
        st.session_state.demo_mode = is_demo

        if is_demo:
            st.info("AIが模範的なセールスを実行します。")
            auto_run = st.toggle("⏱️ オート実行 (10秒)", value=st.session_state.auto_run)
            if auto_run and not st.session_state.auto_run:
                st.session_state.auto_run_first = True
            st.session_state.auto_run = auto_run

            if st.button("⏩ 手動で1ターン進める"):
                if run_demo_turn():
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Current Phase")

    try:
        stage_names = ["OPENING", "SITUATION", "PROBLEM", "IMPLICATION", "NEED_PAYOFF", "CLOSING"]
        if isinstance(st.session_state.current_stage, SPINStage):
            stage_idx = stage_names.index(st.session_state.current_stage.name)
        else:
            stage_idx = 0
            st.session_state.current_stage = SPINStage.OPENING
        st.progress((stage_idx + 1) / len(stage_names))
        st.caption(f"Stage: {st.session_state.current_stage.value}")
    except Exception:
        st.progress(0.17)
        st.caption("Stage: Opening")

    # Error counter (for debugging)
    if st.session_state.get("error_count", 0) > 0:
        st.warning(f"⚠️ Recovered errors: {st.session_state.error_count}")


# --- Main Area ---
if st.session_state.simulation_active:
    col_chat, col_review = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 商談ルーム")

        # Auto-Run Logic
        if st.session_state.demo_mode and st.session_state.auto_run:
            try:
                current_stage = st.session_state.current_stage
                if current_stage == SPINStage.CLOSING and len(st.session_state.messages) > 10:
                    st.success("🎉 デモが完了しました。")
                    st.session_state.auto_run = False
                    st.session_state.auto_run_first = True
                else:
                    if st.session_state.auto_run_first:
                        st.session_state.auto_run_first = False
                        if run_demo_turn():
                            st.rerun()
                    else:
                        timer_ph = st.empty()
                        for i in range(10, 0, -1):
                            timer_ph.info(f"⏳ オート実行中... 次の応答まで: {i}秒")
                            time.sleep(1)
                        timer_ph.empty()
                        if run_demo_turn():
                            st.rerun()
            except Exception as e:
                logger.error(f"Auto-run error: {e}")
                st.session_state.auto_run = False
                st.error("オート実行中にエラーが発生しました。停止しました。")

        # Message History
        for msg in st.session_state.messages:
            try:
                avatar = "🤖" if msg.get("type") == "demo" else ("👤" if msg["role"] == "assistant" else "👔")
                with st.chat_message(msg["role"], avatar=avatar):
                    prefix = "【DEMO】" if msg.get("type") == "demo" else ""
                    st.markdown(f"{prefix} {msg.get('content', '')}")
            except Exception:
                pass

        # Human Input Area
        if not st.session_state.demo_mode:
            if prompt := st.chat_input("提案を入力してください..."):
                try:
                    clean_prompt = sanitize_input(prompt)
                    if clean_prompt:
                        fb, next_stage = evaluate_turn_logic(clean_prompt, st.session_state.current_stage)
                        if fb:
                            st.session_state.current_stage = next_stage
                            st.session_state.messages.append({
                                "role": "user",
                                "content": clean_prompt,
                                "type": "human"
                            })
                            st.session_state.review_log.append({
                                "turn": len(st.session_state.messages) // 2,
                                "is_human": True,
                                "stage": next_stage.value,
                                "feedback": fb
                            })

                            # Customer response
                            cust_resp = "ふむ...（顧客は考え込んでいる）"
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": cust_resp,
                                "type": "ai"
                            })
                            st.rerun()
                except Exception as e:
                    logger.error(f"Input processing error: {e}")
                    st.error("入力の処理中にエラーが発生しました。もう一度お試しください。")

    # Right Column: Manager Review Panel
    with col_review:
        st.subheader("📊 マネージャー評価")

        if st.session_state.review_log:
            try:
                last_review = st.session_state.review_log[-1]
                feedback = last_review.get("feedback", {})
                score = feedback.get("score", 0)
                breakdown = feedback.get("breakdown", {})

                # Score Display
                score_color = "#28a745" if score >= 70 else ("#ffc107" if score >= 40 else "#dc3545")
                st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h1 style="color: {score_color}; margin: 0;">{score}/100</h1>
                    <p style="color: #666;">最新ターンスコア</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Breakdown
                if breakdown:
                    cols = st.columns(2)
                    cols[0].metric("SPIN Flow", f"{breakdown.get('spin_flow', 0)}/40")
                    cols[1].metric("Keywords", f"{breakdown.get('keywords', 0)}/30")
                    cols = st.columns(2)
                    cols[0].metric("Strategy", f"{breakdown.get('strategy', 0)}/20")
                    cols[1].metric("Engagement", f"{breakdown.get('engagement', 0)}/10")

                st.markdown("---")

                # Feedback Box
                status = feedback.get("status", "")
                comment = feedback.get("comment", "")
                box_class = "review-box" if "Good" in status or "Demo" in status else (
                    "review-box-warning" if "Loop" in status else "review-box-danger")
                st.markdown(f"""
                <div class="{box_class}">
                    <strong>{status}</strong><br><br>
                    {comment}
                </div>
                """, unsafe_allow_html=True)

                # Improvement Advice
                improvement = feedback.get("improvement", "")
                if improvement:
                    st.info(f"💡 **改善ポイント:** {improvement}")

                st.markdown("---")

                # History
                with st.expander("📝 過去の評価履歴"):
                    for log in reversed(st.session_state.review_log[:-1][-5:]):
                        log_fb = log.get("feedback", {})
                        st.markdown(f"**Turn {log.get('turn', '?')}** ({log.get('stage', '?')}) - Score: {log_fb.get('score', 0)}")
                        st.caption(log_fb.get("comment", "")[:50] + "...")
                        st.markdown("---")

            except Exception as e:
                logger.error(f"Review panel error: {e}")
                st.info("評価データの読み込み中...")
        else:
            st.info("商談を開始してください。発言に対してリアルタイムで評価を行います。")

        # End Session Button
        if st.button("🏁 セッション終了 & レポート"):
            try:
                human_logs = [l for l in st.session_state.review_log if l.get("is_human")]
                st.markdown("## 📝 Session Report")
                if not human_logs:
                    st.warning("人間による操作記録がありません。")
                else:
                    avg_score = sum(l.get("feedback", {}).get("score", 0) for l in human_logs) / len(human_logs)
                    st.metric("平均スコア", f"{int(avg_score)}/100")
                    for log in human_logs:
                        with st.expander(f"Turn {log.get('turn', '?')}: {log.get('stage', '?')}"):
                            st.write(log.get("feedback", {}).get("comment", ""))
            except Exception as e:
                st.error("レポート生成中にエラーが発生しました。")

else:
    st.title("💬 商談ルーム")
    st.info("👈 左のサイドバーから '新規シナリオ開始' を押してください。")

# --- Test Debug Info (Hidden Element for Automated Testing) ---
import time as _time
try:
    last_feedback = st.session_state.review_log[-1]['feedback'] if st.session_state.review_log else {}
    last_score = last_feedback.get('score', 0)
    last_status = last_feedback.get('status', 'None')
    detected_stage = last_feedback.get('detected_stage', 'Unknown')
    next_stage_debug = last_feedback.get('next_stage', 'Unknown')
    current_stage_name = st.session_state.current_stage.name if isinstance(st.session_state.current_stage, SPINStage) else 'OPENING'
    turn_count = len(st.session_state.review_log)
except Exception:
    last_score = 0
    last_status = 'None'
    detected_stage = 'Unknown'
    next_stage_debug = 'Unknown'
    current_stage_name = 'OPENING'
    turn_count = 0

st.markdown(f"""
<div id="test-debug-info" style="display:none;"
     data-stage="{current_stage_name}"
     data-last-score="{last_score}"
     data-last-status="{last_status}"
     data-detected-stage="{detected_stage}"
     data-next-stage="{next_stage_debug}"
     data-turn-count="{turn_count}"
     data-render-time="{int(_time.time() * 1000)}"
     data-simulation-active="{st.session_state.simulation_active}"
     data-demo-mode="{st.session_state.demo_mode}">
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("🛡️ GWS Agent Architecture Sales Dojo v4.1 (Testable) | Built with Streamlit")
