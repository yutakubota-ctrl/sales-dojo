"""
GWS Agent Sales Dojo v5.0 - The "Closer" Edition
=================================================
Powered by Business Ecosystem Grand Architect

Complete Order-to-Cash flow with:
- Closing Logic (Deal WIN detection)
- Dynamic Customer Reactions
- Manager's Final Report
"""

import streamlit as st
import random
import time
import logging
from enum import Enum

# --- 0. Robust Config & Logging ---
st.set_page_config(layout="wide", page_title="GWS Sales Dojo v5.0 (Final Release)")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def resilient_op(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error: {e}")
            return None
    return wrapper

class SPINStage(Enum):
    OPENING = "Opening (挨拶)"
    SITUATION = "Situation (現状)"
    PROBLEM = "Problem (課題)"
    IMPLICATION = "Implication (深刻化)"
    NEED_PAYOFF = "Need-payoff (解決策)"
    CLOSING = "Closing (契約)"


# --- 1. State Management ---
def init_state():
    defaults = {
        "messages": [],
        "review_log": [],
        "simulation_active": False,
        "customer_persona": {},
        "demo_mode": False,
        "auto_run": False,
        "auto_run_first": True,
        "current_stage_name": "OPENING",  # String for serialization safety
        "deal_closed": False,  # Deal WIN flag
        "error_count": 0
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Validate stage name
    valid_names = [s.name for s in SPINStage]
    if st.session_state.get("current_stage_name") not in valid_names:
        st.session_state.current_stage_name = "OPENING"


def get_current_stage() -> SPINStage:
    """Get current stage as SPINStage enum"""
    name = st.session_state.get("current_stage_name", "OPENING")
    try:
        return SPINStage[name]
    except (KeyError, TypeError):
        return SPINStage.OPENING


def set_current_stage(stage: SPINStage):
    """Set current stage from SPINStage enum"""
    st.session_state.current_stage_name = stage.name


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


# --- 2. Intelligent Logic Engines ---

@resilient_op
def get_customer_reaction(stage: SPINStage, score: int, persona: dict) -> str:
    """
    [Customer Agent]
    Dynamic customer response based on score, stage, and conversation history
    Provides varied responses to avoid repetition
    """
    # Initialize response tracking in session_state
    if "response_counter" not in st.session_state:
        st.session_state.response_counter = {}

    stage_key = stage.name
    if stage_key not in st.session_state.response_counter:
        st.session_state.response_counter[stage_key] = 0

    # Get current counter and increment for next call
    counter = st.session_state.response_counter[stage_key]
    st.session_state.response_counter[stage_key] = counter + 1

    industry = persona.get('industry', '業界')
    position = persona.get('position', '担当者')
    budget = persona.get('budget', '予算')

    if score < 40:
        low_score_responses = [
            f"（{position}は不審そうな顔をしている）...話が飛びすぎていませんか？もう少し現状の話をさせてください。",
            f"（{position}は困惑している）すみません、もう少し順序立てて説明していただけますか？",
            f"（{position}は首をかしげている）その話はまだ早いと思います。まずは状況を整理させてください。"
        ]
        return low_score_responses[counter % len(low_score_responses)]

    # Multiple varied responses per stage
    reactions = {
        SPINStage.OPENING: [
            f"はい、{industry}も変化が早くて大変ですよ。今日はどのようなご用件で？",
            f"お時間いただきありがとうございます。{industry}では今、様々な課題がありますね。",
            f"はじめまして。{industry}の状況についてお話しできればと思います。"
        ],
        SPINStage.SITUATION: [
            "現在はExcelと手入力で対応しています。担当者は3名ほどですね。月末は特に忙しいです。",
            "うちは手作業が多くて...データ入力に週20時間以上かかっています。",
            "基幹システムはあるんですが、Excelでの二重入力が発生していて効率が悪いです。",
            "業務フローは複雑で、担当者によってやり方がバラバラなのが現状です。"
        ],
        SPINStage.PROBLEM: [
            "ええ、まさにその通りです。月末は残業続きで、入力ミスも散見されます...正直、担当者も疲弊しています。",
            "おっしゃる通り、ミスが多くてダブルチェックに時間がかかっています。",
            "確かに課題は認識しています。特に繁忙期のミス率が高くて困っています。",
            "人手不足もあって、チェック体制が不十分なのは否めません。"
        ],
        SPINStage.IMPLICATION: [
            "言われてみれば...ミスによる手戻りコストや、取引先への信頼低下は計り知れませんね。経営層も気にしています。",
            "確かに...このままでは競合に遅れを取る可能性がありますね。",
            "そうですね、人材流出のリスクもあります。若手が辞めてしまうと大変です。",
            "経営陣からも業務効率化の圧力がかかっていて、正直焦っています。"
        ],
        SPINStage.NEED_PAYOFF: [
            "なるほど、AIエージェントがそれを代行してくれるなら、本来の業務に集中できそうです。具体的に聞かせてください。",
            "自動化できれば、戦略的な業務にリソースを割けますね。興味があります。",
            "コスト削減と品質向上の両立ができるなら、ぜひ検討したいです。",
            "その提案は魅力的です。具体的な導入ステップを教えてください。"
        ],
        SPINStage.CLOSING: [
            f"わかりました。その{budget}内のスモールスタートなら、私の決裁で進められます。契約しましょう。",
            f"トライアルから始められるなら安心です。{budget}で進めましょう。",
            f"リスクが低いなら始めてみたいです。契約の手続きを進めてください。",
            f"説得力のある提案でした。上に掛け合ってみます...いえ、私の権限で決めます。"
        ]
    }

    stage_responses = reactions.get(stage, ["なるほど、続けてください。"])
    return stage_responses[counter % len(stage_responses)]


@resilient_op
def get_demo_sales_response(stage: SPINStage, persona: dict) -> str:
    """
    [Top Performer Agent]
    Model answers that progress through SPIN stages
    """
    responses = {
        SPINStage.OPENING: f"本日はお時間をいただきありがとうございます。御社の{persona.get('industry', '業界')}では最近、DX化が課題と伺いますが、状況はいかがですか？",
        SPINStage.SITUATION: "差し支えなければ、現在の請求書処理業務の具体的なフローと、関わっている人数を教えていただけますか？",
        SPINStage.PROBLEM: "ありがとうございます。その手作業のフローにおいて、入力ミスやチェック漏れといった課題は発生していませんか？",
        SPINStage.IMPLICATION: "もしそのミスが発見遅れに繋がった場合、修正にかかる工数や、最悪の場合の取引停止リスクについてはどうお考えですか？",
        SPINStage.NEED_PAYOFF: "もし、当社の『Gemエージェント』がその突合を自動化し、リスクをゼロにできるとしたら、御社の業務改革に役立つと思いませんか？",
        SPINStage.CLOSING: f"では、まずはリスクの高い特定業務に絞り、{persona.get('budget', '予算')}内で収まるPoCプランから開始しませんか？トライアルで効果を検証できます。"
    }
    return responses.get(stage, "提案させてください。")


@resilient_op
def evaluate_turn_logic(user_input: str, current_stage_enum: SPINStage):
    """
    [Manager Agent]
    SPIN progression evaluation logic with improved stage detection
    """
    if not user_input:
        return {"status": "⚠️ Empty", "comment": "入力がありません", "score": 0}, current_stage_enum

    input_text = user_input.lower()

    # Keyword-based stage detection (ordered by priority - later stages checked first)
    stage_keywords = {
        SPINStage.CLOSING: ["契約", "金額", "poc", "始め", "開始", "トライアル", "スモールスタート", "決裁", "進め"],
        SPINStage.NEED_PAYOFF: ["解決", "価値", "できたら", "役立", "提案", "gem", "エージェント", "ai", "自動化", "効率"],
        SPINStage.IMPLICATION: ["影響", "リスク", "コスト", "もし", "深刻", "損失", "遅れ", "危険"],
        SPINStage.PROBLEM: ["課題", "困っ", "ミス", "手間", "問題", "悩み", "大変", "疲弊"],
        SPINStage.SITUATION: ["現状", "フロー", "人数", "どのよう", "状況", "担当", "業務"],
        SPINStage.OPENING: ["はじめ", "挨拶", "時間", "伺い", "よろしく", "ありがとう", "用件"]
    }

    # Detect stage from keywords - check from CLOSING to OPENING (prioritize later stages)
    detected_stage = current_stage_enum
    stage_priority = [SPINStage.CLOSING, SPINStage.NEED_PAYOFF, SPINStage.IMPLICATION,
                      SPINStage.PROBLEM, SPINStage.SITUATION, SPINStage.OPENING]

    for stage in stage_priority:
        keywords = stage_keywords.get(stage, [])
        if any(k in input_text for k in keywords):
            detected_stage = stage
            break

    # Stage progression logic
    stage_list = list(SPINStage)
    curr_idx = stage_list.index(current_stage_enum)
    det_idx = stage_list.index(detected_stage)

    if det_idx > curr_idx + 1:
        # Skipping stages - but allow if we're at NEED_PAYOFF going to CLOSING
        if current_stage_enum == SPINStage.NEED_PAYOFF and detected_stage == SPINStage.CLOSING:
            feedback = {
                "status": "✅ Perfect Progression",
                "comment": f"クロージングへ進みました！",
                "score": 100
            }
            next_stage = detected_stage
        else:
            feedback = {
                "status": "⚠️ Skipping Stages",
                "comment": f"焦りすぎです。現在は「{current_stage_enum.value}」フェーズです。",
                "score": 40
            }
            next_stage = current_stage_enum
    elif det_idx < curr_idx:
        # Loop back - but still allow progression if input is substantial
        if len(input_text) > 50:
            # Long input may contain multiple stage keywords, allow progression
            next_stage = stage_list[min(curr_idx + 1, len(stage_list) - 1)]
            feedback = {
                "status": "✅ Good Progression",
                "comment": "詳細な説明で次へ進みました。",
                "score": 85
            }
        else:
            feedback = {
                "status": "🔄 Loop Back",
                "comment": "確認ありがとうございます。話を進展させましょう。",
                "score": 60
            }
            next_stage = current_stage_enum
    elif det_idx == curr_idx:
        # Same stage - digging deeper, always allow progression with substantial input
        if len(input_text) > 20:
            next_stage = stage_list[min(curr_idx + 1, len(stage_list) - 1)]
            feedback = {
                "status": "✅ Good Progression",
                "comment": f"良い深掘りです。{next_stage.value}へ進みます。",
                "score": 85
            }
        else:
            feedback = {
                "status": "➡️ Deepening",
                "comment": "良い深掘りです。もう少しで次のステージへ進めます。",
                "score": 75
            }
            next_stage = current_stage_enum
    else:
        # Proper advancement
        feedback = {
            "status": "✅ Perfect Progression",
            "comment": f"完璧な流れです。{detected_stage.value}へ進みました。",
            "score": 100
        }
        next_stage = detected_stage

    # Bonus for strategy keywords
    strategy_keywords = ["スモールスタート", "トライアル", "poc", "300万", "500万", "1000万"]
    if any(k in input_text for k in strategy_keywords):
        feedback["score"] = min(feedback["score"] + 10, 100)
        feedback["comment"] += " 戦略的なアプローチです！"

    feedback["detected_stage"] = detected_stage.name
    feedback["next_stage"] = next_stage.name

    return feedback, next_stage


# --- 3. UI Layout ---

# Sidebar
with st.sidebar:
    st.title("🏆 GWS Sales Dojo v5")
    st.caption("The Closer Edition")

    # Debug info for automated tests
    current_stage = get_current_stage()
    review_log = st.session_state.get("review_log", [])
    last_feedback = review_log[-1] if review_log else {}

    st.markdown(f"""
    <div id="test-debug-info" style="display:none;"
         data-stage="{current_stage.name}"
         data-deal-closed="{str(st.session_state.deal_closed).lower()}"
         data-turn-count="{len(review_log)}"
         data-last-score="{last_feedback.get('score', 0)}"
         data-last-status="{last_feedback.get('status', 'None')}"
         data-detected-stage="{last_feedback.get('detected_stage', 'Unknown')}"
         data-next-stage="{last_feedback.get('next_stage', 'Unknown')}"
         data-simulation-active="{st.session_state.simulation_active}"
         data-demo-mode="{st.session_state.demo_mode}">
    </div>
    """, unsafe_allow_html=True)

    if st.button("🆕 新規シナリオ開始", type="primary"):
        st.session_state.customer_persona = {
            "industry": random.choice(["物流", "金融", "製造", "ヘルスケア", "SaaS"]),
            "position": random.choice(["業務改革部長", "DX推進室長", "事業部長"]),
            "personality": random.choice(["慎重派", "革新的", "現場重視"]),
            "budget": random.choice(["300万円", "500万円", "1000万円"])
        }
        st.session_state.messages = []
        st.session_state.review_log = []
        set_current_stage(SPINStage.OPENING)
        st.session_state.simulation_active = True
        st.session_state.deal_closed = False
        st.session_state.auto_run = False
        st.session_state.auto_run_first = True

        # Initial customer message
        p = st.session_state.customer_persona
        msg = f"（{p['industry']}業界 / {p['position']}）\nはい、どういったご用件でしょうか？ {p['personality']}なので、手短にお願いします。"
        st.session_state.messages.append({"role": "assistant", "content": msg, "type": "ai"})
        st.rerun()

    if st.session_state.simulation_active and not st.session_state.deal_closed:
        st.markdown("---")
        st.session_state.demo_mode = st.toggle("🤖 デモモード", value=st.session_state.demo_mode)

        if st.session_state.demo_mode:
            st.session_state.auto_run = st.toggle("⏱️ オート実行 (最後まで)", value=st.session_state.auto_run)
            if st.button("⏩ 手動で1ターン進める"):
                # Trigger one demo turn
                persona = safe_get_persona()
                current = get_current_stage()
                demo_text = get_demo_sales_response(current, persona)

                if demo_text:
                    fb, next_st = evaluate_turn_logic(demo_text, current)
                    if fb:
                        st.session_state.messages.append({"role": "user", "content": demo_text, "type": "demo"})
                        st.session_state.review_log.append({
                            "turn": len(st.session_state.messages) // 2,
                            "is_human": False,
                            "score": fb.get("score", 0),
                            "status": fb.get("status", ""),
                            "detected_stage": fb.get("detected_stage", ""),
                            "next_stage": fb.get("next_stage", "")
                        })
                        set_current_stage(next_st)

                        cust_text = get_customer_reaction(next_st, fb.get("score", 0), persona)
                        st.session_state.messages.append({"role": "assistant", "content": cust_text, "type": "ai"})

                        # Check for deal closure - close if we reach CLOSING stage with decent score
                        if next_st == SPINStage.CLOSING and fb.get("score", 0) >= 60:
                            st.session_state.deal_closed = True

                        st.rerun()

    # Progress bar
    st.markdown("---")
    st.markdown("### 📊 Progress")
    phases = list(SPINStage)
    current = get_current_stage()
    curr_idx = phases.index(current)
    progress_val = (curr_idx + (1 if st.session_state.deal_closed else 0)) / len(phases)
    st.progress(progress_val)

    if st.session_state.deal_closed:
        st.success("🎯 DEAL CLOSED!")
    else:
        st.caption(f"Stage: {current.value}")

    # Persona display
    if st.session_state.simulation_active:
        persona = safe_get_persona()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <strong>🎯 Target:</strong><br>
            {persona.get('industry', 'N/A')} / {persona.get('position', 'N/A')}<br>
            <small>予算: {persona.get('budget', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)


# Main Area
if st.session_state.simulation_active:

    # --- Auto-Run Logic ---
    if st.session_state.demo_mode and st.session_state.auto_run and not st.session_state.deal_closed:
        current = get_current_stage()
        persona = safe_get_persona()

        # Check if we've reached closing and should stop
        if current == SPINStage.CLOSING and len(st.session_state.messages) > 10:
            st.session_state.auto_run = False
        else:
            # Execute one turn
            if st.session_state.auto_run_first:
                st.session_state.auto_run_first = False
            else:
                # Show countdown
                timer_ph = st.empty()
                for i in range(3, 0, -1):
                    timer_ph.info(f"⏳ 次のターンまで: {i}秒")
                    time.sleep(1)
                timer_ph.empty()

            demo_text = get_demo_sales_response(current, persona)
            if demo_text:
                fb, next_st = evaluate_turn_logic(demo_text, current)
                if fb:
                    st.session_state.messages.append({"role": "user", "content": demo_text, "type": "demo"})
                    st.session_state.review_log.append({
                        "turn": len(st.session_state.messages) // 2,
                        "is_human": False,
                        "score": fb.get("score", 0),
                        "status": fb.get("status", ""),
                        "detected_stage": fb.get("detected_stage", ""),
                        "next_stage": fb.get("next_stage", "")
                    })
                    set_current_stage(next_st)

                    cust_text = get_customer_reaction(next_st, fb.get("score", 0), persona)
                    st.session_state.messages.append({"role": "assistant", "content": cust_text, "type": "ai"})

                    # Check for deal closure - close if we reach CLOSING stage with decent score
                    if next_st == SPINStage.CLOSING and fb.get("score", 0) >= 60:
                        st.session_state.deal_closed = True
                        st.session_state.auto_run = False
                        st.balloons()

                    st.rerun()

    # --- Chat History ---
    st.subheader("💬 商談ルーム")

    for idx, msg in enumerate(st.session_state.messages):
        avatar = "🤖" if msg.get("type") == "demo" else ("👤" if msg["role"] == "user" else "🧑‍💼")
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

            # Show score for user messages
            if msg["role"] == "user":
                log_idx = idx // 2
                if log_idx < len(st.session_state.review_log):
                    log = st.session_state.review_log[log_idx]
                    score = log.get("score", 0)
                    status = log.get("status", "")
                    color = "green" if score >= 80 else ("orange" if score >= 60 else "red")
                    st.caption(f"📊 {status} (Score: {score})")

    # --- Human Input ---
    if not st.session_state.demo_mode and not st.session_state.deal_closed:
        if prompt := st.chat_input("提案を入力してください..."):
            current = get_current_stage()
            fb, next_st = evaluate_turn_logic(prompt, current)

            if fb:
                st.session_state.messages.append({"role": "user", "content": prompt, "type": "human"})
                st.session_state.review_log.append({
                    "turn": len(st.session_state.messages) // 2,
                    "is_human": True,
                    "score": fb.get("score", 0),
                    "status": fb.get("status", ""),
                    "detected_stage": fb.get("detected_stage", ""),
                    "next_stage": fb.get("next_stage", "")
                })
                set_current_stage(next_st)

                persona = safe_get_persona()
                cust_text = get_customer_reaction(next_st, fb.get("score", 0), persona)
                st.session_state.messages.append({"role": "assistant", "content": cust_text, "type": "ai"})

                # Check for deal closure - close if we reach CLOSING stage with decent score
                if next_st == SPINStage.CLOSING and fb.get("score", 0) >= 60:
                    st.session_state.deal_closed = True
                    st.balloons()

                st.rerun()

    # --- Final Report (when deal is closed) ---
    if st.session_state.deal_closed:
        st.success("🎉 CONGRATULATIONS! 商談成立です。")

        with st.expander("📝 Manager's Final Report", expanded=True):
            logs = st.session_state.review_log
            if logs:
                avg_score = sum(l.get("score", 0) for l in logs) / len(logs)
                human_turns = sum(1 for l in logs if l.get("is_human", False))

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("🏆 Final Score", f"{int(avg_score)}/100")
                    st.metric("📊 Total Turns", len(logs))
                    st.metric("👤 Human Turns", human_turns)

                with col2:
                    st.write("##### 📋 Review Summary")
                    if avg_score >= 90:
                        st.success("🌟 Excellent! 完璧なSPIN営業でした。各フェーズの移行もスムーズで、顧客の課題に深く共感できています。")
                    elif avg_score >= 75:
                        st.info("👍 Good! 商談成立おめでとうございます。いくつかの改善点はありますが、全体的に良い流れでした。")
                    else:
                        st.warning("⚠️ Needs Improvement: 商談は成立しましたが、強引な場面が見られました。特に「課題の深掘り」を意識しましょう。")

                # Turn-by-turn analysis
                st.markdown("##### 📈 Turn-by-Turn Analysis")
                for i, log in enumerate(logs):
                    score = log.get("score", 0)
                    status = log.get("status", "")
                    icon = "✅" if score >= 80 else ("⚠️" if score >= 60 else "❌")
                    st.write(f"{icon} Turn {i+1}: {status} (Score: {score})")
            else:
                st.write("No data available.")

        if st.button("🔄 次の商談へ (Reset)"):
            st.session_state.simulation_active = False
            st.session_state.deal_closed = False
            st.rerun()

else:
    st.title("🏆 GWS Sales Dojo v5.0")
    st.markdown("### The Closer Edition")
    st.info("👈 左側のサイドバーから '新規シナリオ開始' を押してください。")

    st.markdown("""
    #### 🎯 このアプリについて

    SPIN営業フレームワークを学ぶためのロールプレイシミュレーターです。

    **SPINとは:**
    - **S**ituation: 顧客の現状を把握する
    - **P**roblem: 課題を明確にする
    - **I**mplication: 課題の深刻さを認識させる
    - **N**eed-payoff: 解決策の価値を伝える

    **使い方:**
    1. 「新規シナリオ開始」でロールプレイを開始
    2. 手動で提案を入力するか、デモモードでお手本を見る
    3. CLOSING まで進めて商談を成立させましょう！
    """)

# Footer
st.markdown("---")
st.caption("🏆 GWS Agent Architecture Sales Dojo v5.0 (The Closer Edition) | Built with Streamlit")
