"""
GWS Agent Architecture Sales Dojo v3.1
======================================
Powered by Business Ecosystem Grand Architect

Features:
- Auto-Pilot Demo Mode with 10-second interval
- Persona Editor for custom scenarios
- SPIN Selling Framework analysis
- Manager Evaluation Panel
"""

import streamlit as st
import random
import time
from enum import Enum

# --- 0. Constants & Config ---
st.set_page_config(layout="wide", page_title="GWS Sales Dojo v3.1 (Auto-Pilot & Editor)")

# SPIN Stages Definition
class SPINStage(Enum):
    OPENING = "Opening (挨拶・ラポール)"
    SITUATION = "Situation (現状把握)"
    PROBLEM = "Problem (課題抽出)"
    IMPLICATION = "Implication (問題の深刻化)"
    NEED_PAYOFF = "Need-payoff (解決の価値・提案)"
    CLOSING = "Closing (合意形成)"

# --- 1. State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "review_log" not in st.session_state:
    st.session_state.review_log = []
if "simulation_active" not in st.session_state:
    st.session_state.simulation_active = False
if "customer_persona" not in st.session_state:
    st.session_state.customer_persona = {}
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False
if "auto_run" not in st.session_state:
    st.session_state.auto_run = False
if "current_stage" not in st.session_state:
    st.session_state.current_stage = SPINStage.OPENING
if "auto_run_first" not in st.session_state:
    st.session_state.auto_run_first = True

# Validate current_stage is a valid SPINStage enum (fix for corrupted sessions)
if not isinstance(st.session_state.current_stage, SPINStage):
    st.session_state.current_stage = SPINStage.OPENING

# --- 2. Logic Engines (Simulated LLMs) ---

def get_demo_sales_response(history, stage, persona):
    """[The Top Performer Agent]"""
    responses = {
        SPINStage.OPENING: f"本日はお時間をいただきありがとうございます。{persona['industry']}業界では最近、人手不足が深刻だと伺いますが、御社の状況はいかがでしょうか？",
        SPINStage.SITUATION: "なるほど。具体的には、請求書の処理業務には現在どのくらいの人数と時間を割かれているのですか？",
        SPINStage.PROBLEM: "それは大きな負担ですね。特に月末の締め処理などで、ミスが発生したり、残業が増えたりする課題はございませんか？",
        SPINStage.IMPLICATION: "もしそのミスが見過ごされた場合、取引先との信頼関係や、修正にかかるコストはどれくらいの影響になるとお考えでしょうか？",
        SPINStage.NEED_PAYOFF: "ありがとうございます。もし、その『確認作業』自体をAIエージェントが代行し、担当者様は『最終承認ボタンを押すだけ』になれば、本来注力すべき業務に時間を割けると思いませんか？",
        SPINStage.CLOSING: f"まずはその請求書処理の部分だけ、300万円未満（{persona['budget']}の範囲内）のトライアルとして導入し、効果を検証してみませんか？"
    }
    return responses.get(stage, "ご提案があります...")

def evaluate_turn_logic(user_input, current_stage_enum):
    """[The Manager Agent] SPIN分析と段階飛ばしのチェック + 詳細スコア"""
    if not isinstance(current_stage_enum, SPINStage):
        current_stage_enum = SPINStage.OPENING

    feedback = {}
    detected_stage = SPINStage.SITUATION

    input_text = user_input.lower()

    if "はじめまして" in input_text or "ありがとう" in input_text:
        detected_stage = SPINStage.OPENING
    elif "現状" in input_text or "どのような" in input_text or "人数" in input_text:
        detected_stage = SPINStage.SITUATION
    elif "困って" in input_text or "課題" in input_text or "ミス" in input_text:
        detected_stage = SPINStage.PROBLEM
    elif "影響" in input_text or "コスト" in input_text or "リスク" in input_text:
        detected_stage = SPINStage.IMPLICATION
    elif "解決" in input_text or "AI" in input_text or "Gem" in input_text or "提案" in input_text:
        detected_stage = SPINStage.NEED_PAYOFF
    elif "契約" in input_text or "金額" in input_text or "トライアル" in input_text:
        detected_stage = SPINStage.CLOSING

    stage_order = [s for s in SPINStage]
    current_index = stage_order.index(current_stage_enum)
    detected_index = stage_order.index(detected_stage)

    # 詳細スコア計算
    breakdown = {"spin_flow": 0, "keywords": 0, "strategy": 0, "engagement": 0}

    # SPIN Flow Score (40点満点)
    if detected_index > current_index + 1:
        feedback["status"] = "⚠️ Alert: Skipping Stages"
        feedback["comment"] = f"段階を飛ばしすぎています！現在は「{current_stage_enum.value.split(' ')[0]}」フェーズです。"
        breakdown["spin_flow"] = 10
        next_stage = current_stage_enum
    elif detected_index < current_index:
        feedback["status"] = "🔄 Loop Back"
        feedback["comment"] = "前のフェーズに戻りました。確認は良いですが、進展させましょう。"
        breakdown["spin_flow"] = 25
        next_stage = current_stage_enum
    else:
        feedback["status"] = "✅ Good Progression"
        feedback["comment"] = f"順調です。{detected_stage.value} の意図が伝わりました。"
        breakdown["spin_flow"] = 40
        next_stage = detected_stage

    # Keywords Score (30点満点)
    good_keywords = ["Gem", "エージェント", "承認", "人間", "循環", "連携", "リルート"]
    keyword_hits = sum(1 for kw in good_keywords if kw in user_input)
    breakdown["keywords"] = min(keyword_hits * 10, 30)

    # Strategy Score (20点満点)
    strategy_keywords = ["スモールスタート", "トライアル", "PoC", "まずは", "300万", "500万"]
    strategy_hits = sum(1 for kw in strategy_keywords if kw in user_input)
    breakdown["strategy"] = min(strategy_hits * 10, 20)

    # Engagement Score (10点満点)
    if len(user_input) > 50:
        breakdown["engagement"] = 10
    elif len(user_input) > 20:
        breakdown["engagement"] = 5

    feedback["score"] = sum(breakdown.values())
    feedback["breakdown"] = breakdown
    feedback["improvement"] = get_improvement_advice(breakdown)

    return feedback, next_stage

def get_improvement_advice(breakdown):
    """スコアに基づいた改善アドバイスを生成"""
    advice = []
    if breakdown["spin_flow"] < 30:
        advice.append("SPINの順序を守り、段階を飛ばさないようにしましょう。")
    if breakdown["keywords"] < 15:
        advice.append("Gem、承認フロー、連携などの技術キーワードを使いましょう。")
    if breakdown["strategy"] < 10:
        advice.append("スモールスタートやトライアル提案で着地点を示しましょう。")
    if breakdown["engagement"] < 5:
        advice.append("もう少し詳しく説明を加えましょう。")
    return " ".join(advice) if advice else "素晴らしい提案です！この調子で続けましょう。"

def run_demo_turn():
    """デモモードの1ターンを実行"""
    if not isinstance(st.session_state.current_stage, SPINStage):
        st.session_state.current_stage = SPINStage.OPENING

    persona = st.session_state.customer_persona
    if not persona or "industry" not in persona:
        persona = {"industry": "製造", "position": "部長", "personality": "論理的", "budget": "500万円"}
        st.session_state.customer_persona = persona

    current_stage = st.session_state.current_stage
    demo_input = get_demo_sales_response(st.session_state.messages, current_stage, persona)

    stage_order = list(SPINStage)
    current_idx = stage_order.index(current_stage)
    next_stage = stage_order[current_idx + 1] if current_idx < len(stage_order) - 1 else SPINStage.CLOSING

    st.session_state.current_stage = next_stage
    st.session_state.messages.append({"role": "user", "content": demo_input, "type": "demo"})
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

    time.sleep(0.5)
    customer_responses = {
        SPINStage.OPENING: f"はい、{persona['industry']}の現場は確かに人手不足です。何かお考えがあるのですか？",
        SPINStage.SITUATION: "そうですね、請求書処理には3名で月に約40時間かけています。",
        SPINStage.PROBLEM: "おっしゃる通り、月末は特に残業が増えますね。ミスも時々発生します。",
        SPINStage.IMPLICATION: "確かに、取引先への謝罪や修正作業で余計なコストがかかっていますね...",
        SPINStage.NEED_PAYOFF: "なるほど、最終承認だけで済むなら魅力的ですね。具体的にはどういう形で始められますか？",
        SPINStage.CLOSING: "その条件なら前向きに検討できそうです。社内で相談してみます。"
    }
    cust_resp = customer_responses.get(current_stage, "なるほど、続けてください。")
    st.session_state.messages.append({"role": "assistant", "content": cust_resp, "type": "ai"})


# --- 3. UI Components ---

def init_scenario():
    st.session_state.messages = []
    st.session_state.review_log = []
    st.session_state.simulation_active = True
    st.session_state.current_stage = SPINStage.OPENING
    st.session_state.auto_run = False
    st.session_state.auto_run_first = True

    if not st.session_state.customer_persona:
        st.session_state.customer_persona = {
            "industry": random.choice(["物流", "金融", "製造", "ヘルスケア", "SaaS"]),
            "position": random.choice(["業務改革部長", "DX推進室長", "事業部長", "課長"]),
            "personality": random.choice(["慎重派。コスト意識が高い。", "革新的だが実績を重視。", "現場からの反発を懸念。"]),
            "budget": random.choice(["300万円", "500万円", "1000万円"])
        }

    p = st.session_state.customer_persona
    msg = f"（{p['industry']}業界 / {p['position']}）\nはい、どういったご用件でしょうか？ {p['personality']} なので、手短にお願いします。"
    st.session_state.messages.append({"role": "assistant", "content": msg, "type": "ai"})

def get_score_class(score):
    if score >= 70: return "score-high"
    elif score >= 40: return "score-mid"
    return "score-low"

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

# Sidebar Controls
with st.sidebar:
    st.title("🧩 GWS Sales Dojo v3.1")

    with st.expander("👤 ペルソナ設定・編集", expanded=True):
        curr_p = st.session_state.customer_persona if st.session_state.customer_persona else {
            "industry": "製造", "position": "部長", "personality": "論理的", "budget": "500万円"
        }
        p_industry = st.text_input("業界", value=curr_p.get("industry", ""))
        p_position = st.text_input("役職", value=curr_p.get("position", ""))
        p_personality = st.text_input("性格", value=curr_p.get("personality", ""))
        p_budget = st.text_input("予算", value=curr_p.get("budget", ""))

        if st.button("✅ 設定を反映してリセット"):
            st.session_state.customer_persona = {
                "industry": p_industry, "position": p_position,
                "personality": p_personality, "budget": p_budget
            }
            init_scenario()
            st.rerun()

    st.markdown("---")

    if st.button("🆕 新規シナリオ開始 (ランダム)", type="primary"):
        st.session_state.customer_persona = {}
        init_scenario()
        st.rerun()

    if st.session_state.simulation_active:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <strong>🎯 Target:</strong><br>
            {st.session_state.customer_persona.get('industry', 'N/A')} / {st.session_state.customer_persona.get('position', 'N/A')}<br>
            <small>予算: {st.session_state.customer_persona.get('budget', 'N/A')}</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        is_demo = st.toggle("🤖 デモモード (Auto-Pilot)", value=st.session_state.demo_mode)
        st.session_state.demo_mode = is_demo

        if is_demo:
            st.info("AIが模範的なセールスを行います。")
            auto_run = st.toggle("⏱️ オート実行 (10秒間隔)", value=st.session_state.auto_run)
            if auto_run and not st.session_state.auto_run:
                st.session_state.auto_run_first = True
            st.session_state.auto_run = auto_run

            if st.button("⏩ 手動で1ターン進める"):
                run_demo_turn()
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Current Phase")
    stage_names = ["OPENING", "SITUATION", "PROBLEM", "IMPLICATION", "NEED_PAYOFF", "CLOSING"]
    try:
        stage_idx = stage_names.index(st.session_state.current_stage.name)
        st.progress((stage_idx + 1) / len(stage_names))
        st.caption(f"Stage: {st.session_state.current_stage.value}")
    except (ValueError, AttributeError):
        st.session_state.current_stage = SPINStage.OPENING
        st.progress(1 / len(stage_names))
        st.caption(f"Stage: {SPINStage.OPENING.value}")


# Main Area with Two Columns
if st.session_state.simulation_active:
    col_chat, col_review = st.columns([2, 1])

    with col_chat:
        st.subheader("💬 商談ルーム")

        # Auto-Run Logic
        if st.session_state.demo_mode and st.session_state.auto_run:
            if st.session_state.current_stage == SPINStage.CLOSING and len(st.session_state.messages) > 10:
                st.success("🎉 デモが完了しました。")
                st.session_state.auto_run = False
                st.session_state.auto_run_first = True
            else:
                if st.session_state.auto_run_first:
                    st.session_state.auto_run_first = False
                    run_demo_turn()
                    st.rerun()
                else:
                    timer_ph = st.empty()
                    for i in range(10, 0, -1):
                        timer_ph.info(f"⏳ オート実行中... 次の応答まで: {i}秒")
                        time.sleep(1)
                    timer_ph.empty()
                    run_demo_turn()
                    st.rerun()

        # Message History
        for msg in st.session_state.messages:
            avatar = "🤖" if msg.get("type") == "demo" else ("👤" if msg["role"] == "assistant" else "👔")
            with st.chat_message(msg["role"], avatar=avatar):
                prefix = "【DEMO】" if msg.get("type") == "demo" else ""
                st.markdown(f"{prefix} {msg['content']}")

        # Human Input Area
        if not st.session_state.demo_mode:
            if prompt := st.chat_input("あなたのターンです。SPINを意識して入力..."):
                fb, next_stage = evaluate_turn_logic(prompt, st.session_state.current_stage)
                st.session_state.current_stage = next_stage
                st.session_state.messages.append({"role": "user", "content": prompt, "type": "human"})
                st.session_state.review_log.append({
                    "turn": len(st.session_state.messages) // 2,
                    "is_human": True,
                    "stage": next_stage.value,
                    "feedback": fb
                })
                time.sleep(0.5)
                cust_resp = "ふむ...（顧客は考え込んでいる）"
                st.session_state.messages.append({"role": "assistant", "content": cust_resp, "type": "ai"})
                st.rerun()

    # Right Column: Manager Review Panel
    with col_review:
        st.subheader("📊 マネージャー評価")

        if st.session_state.review_log:
            last_review = st.session_state.review_log[-1]
            score = last_review['feedback']['score']
            breakdown = last_review['feedback'].get('breakdown', {})

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
            status = last_review['feedback']['status']
            comment = last_review['feedback']['comment']
            box_class = "review-box" if "Good" in status or "Demo" in status else ("review-box-warning" if "Loop" in status else "review-box-danger")
            st.markdown(f"""
            <div class="{box_class}">
                <strong>{status}</strong><br><br>
                {comment}
            </div>
            """, unsafe_allow_html=True)

            # Improvement Advice
            improvement = last_review['feedback'].get('improvement', '')
            if improvement:
                st.info(f"💡 **改善ポイント:** {improvement}")

            st.markdown("---")

            # History
            with st.expander("📝 過去の評価履歴"):
                for log in reversed(st.session_state.review_log[:-1]):
                    st.markdown(f"**Turn {log['turn']}** ({log['stage']}) - Score: {log['feedback']['score']}")
                    st.caption(log['feedback']['comment'][:50] + "...")
                    st.markdown("---")
        else:
            st.info("商談を開始してください。発言に対してリアルタイムで評価を行います。")

        # End Session Button
        if st.button("🏁 セッション終了 & レポート"):
            human_logs = [l for l in st.session_state.review_log if l.get("is_human")]
            st.markdown("## 📝 Session Report")
            if not human_logs:
                st.warning("人間による操作記録がありません。")
            else:
                avg_score = sum(l["feedback"]["score"] for l in human_logs) / len(human_logs)
                st.metric("平均スコア", f"{int(avg_score)}/100")
                for log in human_logs:
                    with st.expander(f"Turn {log['turn']}: {log['stage']}"):
                        st.write(log['feedback']['comment'])

else:
    st.title("💬 商談ルーム")
    st.info("👈 左のサイドバーから '新規シナリオ開始' または 'ペルソナ設定' を行ってください。")

# Footer
st.markdown("---")
st.caption("🧩 GWS Agent Architecture Sales Dojo v3.1 | Built with Streamlit")
