"""
GWS Agent Architecture Sales Dojo v3.0
======================================
Powered by Business Ecosystem Grand Architect

Features:
- Auto-Pilot Demo Mode with 30-second interval
- Persona Editor for custom scenarios
- SPIN Selling Framework analysis
"""

import streamlit as st
import random
import time
from enum import Enum

# --- 0. Constants & Config ---
st.set_page_config(layout="wide", page_title="GWS Sales Dojo v3.0 (Auto-Pilot & Editor)")

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

# --- 2. Logic Engines (Simulated LLMs) ---

def get_demo_sales_response(history, stage, persona):
    """
    [The Top Performer Agent]
    本来はLLMが「文脈に沿った最強の営業トーク」を生成する場所。
    """
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
    """
    [The Manager Agent]
    SPIN分析と段階飛ばしのチェックを行う。
    """
    feedback = {}
    detected_stage = SPINStage.SITUATION  # Default placeholder

    # 簡易キーワード分析 (本番はLLMで判定)
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

    # Logic: Stage Skipping Check
    stage_order = [s for s in SPINStage]
    current_index = stage_order.index(current_stage_enum)
    detected_index = stage_order.index(detected_stage)

    # 評価コメント生成
    if detected_index > current_index + 1:
        feedback["status"] = "⚠️ Alert: Skipping Stages"
        feedback["comment"] = f"段階を飛ばしすぎています！ 現在はまだ「{current_stage_enum.value.split(' ')[0]}」フェーズです。相手の課題（Problem/Implication）を深掘りする前に解決策（Need-payoff）を提示しても、押し売りに聞こえます。"
        feedback["score"] = 40
        next_stage = current_stage_enum  # 進ませない
    elif detected_index < current_index:
        feedback["status"] = "🔄 Loop Back"
        feedback["comment"] = f"前のフェーズの話に戻りましたね。確認としてはOKですが、話が進展していません。"
        feedback["score"] = 60
        next_stage = current_stage_enum
    else:
        feedback["status"] = "✅ Good Progression"
        feedback["comment"] = f"順調です。{detected_stage.value} の意図が伝わりました。"
        feedback["score"] = 90
        next_stage = detected_stage  # ステージ進行

    return feedback, next_stage

def run_demo_turn():
    """デモモードの1ターンを実行する処理"""
    demo_input = get_demo_sales_response(
        st.session_state.messages,
        st.session_state.current_stage,
        st.session_state.customer_persona
    )

    fb, next_stage = evaluate_turn_logic(demo_input, st.session_state.current_stage)
    st.session_state.current_stage = next_stage

    st.session_state.messages.append({"role": "user", "content": demo_input, "type": "demo"})
    st.session_state.review_log.append({
        "turn": len(st.session_state.messages) // 2,
        "is_human": False,
        "stage": next_stage.value,
        "feedback": fb
    })

    # Customer Response (Simulated)
    time.sleep(0.5)
    cust_resp = f"なるほど、{st.session_state.customer_persona['industry']}の現場としては一理ありますね。（関心が高まった）"
    st.session_state.messages.append({"role": "assistant", "content": cust_resp, "type": "ai"})


# --- 3. UI Components ---

def init_scenario():
    st.session_state.messages = []
    st.session_state.review_log = []
    st.session_state.simulation_active = True
    st.session_state.current_stage = SPINStage.OPENING
    st.session_state.auto_run = False  # Reset auto run on new scenario

    # Check if persona is set, if not random
    if not st.session_state.customer_persona:
        st.session_state.customer_persona = {
            "industry": random.choice(["物流", "金融", "製造", "ヘルスケア", "SaaS"]),
            "position": random.choice(["業務改革部長", "DX推進室長", "事業部長", "課長"]),
            "personality": random.choice(["慎重派。コスト意識が高い。", "革新的だが実績を重視。", "現場からの反発を懸念。"]),
            "budget": random.choice(["300万円", "500万円", "1000万円"])
        }

    # Initial Customer Message
    p = st.session_state.customer_persona
    msg = f"（{p['industry']}業界 / {p['position']}）\nはい、どういったご用件でしょうか？ {p['personality']} なので、手短にお願いします。"
    st.session_state.messages.append({"role": "assistant", "content": msg, "type": "ai"})


# Sidebar Controls
with st.sidebar:
    st.title("🧩 GWS Sales Dojo v3.0")

    # --- Persona Editor ---
    with st.expander("👤 ペルソナ設定・編集", expanded=True):
        # Default values or current state
        curr_p = st.session_state.customer_persona if st.session_state.customer_persona else {
            "industry": "製造", "position": "部長", "personality": "論理的", "budget": "500万円"
        }

        p_industry = st.text_input("業界 (Industry)", value=curr_p.get("industry", ""))
        p_position = st.text_input("役職 (Position)", value=curr_p.get("position", ""))
        p_personality = st.text_input("性格 (Personality)", value=curr_p.get("personality", ""))
        p_budget = st.text_input("予算 (Budget)", value=curr_p.get("budget", ""))

        if st.button("✅ 設定を反映してリセット"):
            st.session_state.customer_persona = {
                "industry": p_industry,
                "position": p_position,
                "personality": p_personality,
                "budget": p_budget
            }
            init_scenario()
            st.rerun()

    st.markdown("---")

    # 1. Start/Reset
    if st.button("🆕 新規シナリオ開始 (ランダム)", type="primary"):
        st.session_state.customer_persona = {}  # Clear to random
        init_scenario()
        st.rerun()

    if st.session_state.simulation_active:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
            <strong>🎯 Target:</strong><br>
            {st.session_state.customer_persona['industry']} / {st.session_state.customer_persona['position']}<br>
            <small>予算: {st.session_state.customer_persona['budget']}</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        # 2. Demo Mode Toggle
        is_demo = st.toggle("🤖 デモモード (Auto-Pilot)", value=st.session_state.demo_mode)
        st.session_state.demo_mode = is_demo

        if is_demo:
            st.info("AIが模範的なセールスを行います。")

            # Auto Run Switch
            auto_run = st.toggle("⏱️ オート実行 (30秒間隔)", value=st.session_state.auto_run)
            st.session_state.auto_run = auto_run

            if st.button("⏩ 手動で1ターン進める"):
                run_demo_turn()
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Current Phase")

    # Safe stage index calculation
    stage_names = ["OPENING", "SITUATION", "PROBLEM", "IMPLICATION", "NEED_PAYOFF", "CLOSING"]
    try:
        stage_idx = stage_names.index(st.session_state.current_stage.name)
        st.progress((stage_idx + 1) / len(stage_names))
        st.caption(f"Stage: {st.session_state.current_stage.value}")
    except (ValueError, AttributeError):
        st.session_state.current_stage = SPINStage.OPENING
        st.progress(1 / len(stage_names))
        st.caption(f"Stage: {SPINStage.OPENING.value}")


# Main Chat Area
st.title("💬 商談ルーム")

if st.session_state.simulation_active:

    # Auto-Run Logic (Place at top of main area to handle updates)
    if st.session_state.demo_mode and st.session_state.auto_run:
        # Check if we should stop (e.g. End of game)
        if st.session_state.current_stage == SPINStage.CLOSING and len(st.session_state.messages) > 10:
            st.success("🎉 デモが完了しました。")
            st.session_state.auto_run = False
        else:
            # Placeholder for countdown
            timer_ph = st.empty()
            # 30 seconds countdown
            for i in range(30, 0, -1):
                timer_ph.info(f"⏳ オート実行中... 次の応答まで: {i}秒 (停止するにはサイドバーのスイッチをOFFにしてください)")
                time.sleep(1)

            timer_ph.empty()
            run_demo_turn()
            st.rerun()

    # 1. Message History
    for msg in st.session_state.messages:
        avatar = "🤖" if msg.get("type") == "demo" else ("👤" if msg["role"] == "assistant" else "👔")
        with st.chat_message(msg["role"], avatar=avatar):
            prefix = "【DEMO】" if msg.get("type") == "demo" else ""
            st.markdown(f"{prefix} {msg['content']}")

            # Show mini-feedback for Demo/Human actions
            if msg["role"] == "user":
                # Find corresponding log
                log_idx = (st.session_state.messages.index(msg)) // 2
                if log_idx < len(st.session_state.review_log):
                    log = st.session_state.review_log[log_idx]
                    color = "orange" if "Alert" in log["feedback"]["status"] else "green"
                    st.markdown(f":{color}[_{log['feedback']['status']} (Stage: {log['stage']})_]")

    # 2. Human Input Area (Only if Demo Mode is OFF)
    if not st.session_state.demo_mode:
        if prompt := st.chat_input("あなたのターンです。SPINを意識して入力..."):
            # Human Logic
            fb, next_stage = evaluate_turn_logic(prompt, st.session_state.current_stage)
            st.session_state.current_stage = next_stage

            st.session_state.messages.append({"role": "user", "content": prompt, "type": "human"})
            st.session_state.review_log.append({
                "turn": len(st.session_state.messages) // 2,
                "is_human": True,  # Filter Target
                "stage": next_stage.value,
                "feedback": fb
            })

            # Customer Response
            time.sleep(1)
            cust_resp = "ふむ...（顧客は考え込んでいる）"
            st.session_state.messages.append({"role": "assistant", "content": cust_resp, "type": "ai"})
            st.rerun()

    # 3. Final Feedback
    st.markdown("---")
    if st.button("🏁 セッション終了 & 評価"):
        human_logs = [l for l in st.session_state.review_log if l["is_human"]]

        st.markdown("## 📝 Human Performance Review")
        if not human_logs:
            st.warning("人間による操作記録がありません（すべてデモモードでした）。")
        else:
            score_avg = sum([l["feedback"]["score"] for l in human_logs]) / len(human_logs)
            st.metric("Average Score", f"{int(score_avg)} / 100")

            for log in human_logs:
                with st.expander(f"Turn {log['turn']} : {log['stage']}"):
                    st.info(log['feedback']['comment'])
                    if log['feedback']['score'] < 60:
                        st.error("改善点: 段階を急ぎすぎています。SPINの順序を守ってください。")

else:
    st.info("👈 左のサイドバーから '新規シナリオ開始' または 'ペルソナ設定' を行ってください。")

# Footer
st.markdown("---")
st.caption("🧩 GWS Agent Architecture Sales Dojo v3.0 | Built with Streamlit")
