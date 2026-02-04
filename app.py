"""
GWS Agent Architecture Sales Dojo
==================================
Powered by Business Ecosystem Grand Architect

A sales training simulator with dual AI agents:
- Customer Agent: Simulates a skeptical department head
- Manager Agent: Reviews and scores sales rep responses
"""

import streamlit as st
import random
import time
import os
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Try to import Anthropic ---
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# --- Try to import Audio Recording ---
try:
    from audio_recorder_streamlit import audio_recorder
    import speech_recognition as sr
    import io
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using Google Speech Recognition."""
    if not AUDIO_AVAILABLE:
        return None

    recognizer = sr.Recognizer()

    # Convert audio bytes to AudioFile
    audio_file = io.BytesIO(audio_bytes)

    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ja-JP")
            return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None
    except Exception:
        # Try alternative approach with WAV header
        return None

# --- Configuration & Constants ---
INDUSTRIES = ["製造業", "SaaS", "金融", "物流", "ヘルスケア", "建設", "小売", "不動産"]
BUDGETS = ["300万円（部内予算）", "500万円（部内予算）", "1000万円（部門予算）", "2000万円（全社予算）"]
POSITIONS = ["部長", "課長", "事業部長", "DX推進室長"]
PERSONALITIES = [
    "論理的だが新しい技術には慎重。ROIとセキュリティを重視する。",
    "革新的な技術に興味があるが、導入実績を重視する。",
    "コスト削減に強い関心がある。具体的な数字での説明を好む。",
    "現場からの反発を懸念している。導入の容易さを重視する。",
    "過去にRPA導入で失敗経験あり。例外処理への対応を重視する。"
]

# --- LLM System Prompts ---
CUSTOMER_SYSTEM_PROMPT = """あなたは日本企業の{position}です。{industry}業界で働いており、以下の特性を持っています：

【ペルソナ設定】
- 役職: {position}
- 業界: {industry}
- 予算: {budget}
- 性格: {personality}
- 課題: {pain_point}

【行動指針】
1. 「魔法のように何でも解決する」という言葉は信じない
2. 具体的な仕組み、セキュリティ、ROIについて質問する
3. 以下のキーワードが営業から出た場合、信頼度が上がる：
   - エラー時のリルート（別ルートでの再アプローチ）
   - 人間が最終承認するゲートキーパー機能
   - 既存のGoogle Workspace（Spreadsheet/Gmail）とのシームレスな統合
   - Micro-Agent（単一責任の小さなエージェント）
   - 有機的循環（Organic Looping）
4. 信頼度が上がるにつれて、前向きな姿勢を見せる
5. 最初は懐疑的→興味関心→懸念提示→合意形成という流れで態度を変化させる

【会話スタイル】
- ビジネスパーソンとして礼儀正しく、しかし鋭い質問をする
- 曖昧な回答には追加質問で掘り下げる
- 良い回答には具体的に何が良かったかをほのめかす
- 回答は2-4文程度で簡潔に

現在の営業担当からの発言に対して、上記ペルソナとして自然に応答してください。"""

MANAGER_SYSTEM_PROMPT = """あなたはFDE/DSコンサルタントの統括責任者です。営業担当の発言を厳格に評価します。

【評価基準】
以下の観点で0-100点のスコアと詳細なフィードバックを提供してください：

1. **Micro-Agent Strategy（30点）**
   - 単一責任の原則に基づくエージェント設計への言及
   - 例：「メール解析Gem」と「下書き作成Gem」を分けるなど
   - 汎用的な「何でもできるAI」という説明は0点

2. **動的ステート管理（25点）**
   - エラー時のリルート、状態遷移の説明
   - 例外処理への対応方法

3. **有機的循環（Organic Looping）（25点）**
   - エージェント間の連携、フィードバックループ
   - 単線的な処理ではない説明

4. **Human-in-the-Loop（20点）**
   - 人間の承認・介入ポイントへの言及
   - 最終判断は人間が行う設計思想

【出力形式】
必ず以下のJSON形式で回答してください：
{{
    "score": <0-100の整数>,
    "breakdown": {{
        "micro_agent": <0-30>,
        "state_management": <0-25>,
        "organic_looping": <0-25>,
        "human_in_loop": <0-20>
    }},
    "feedback": [
        "フィードバックポイント1",
        "フィードバックポイント2"
    ],
    "improvement": "改善のためのアドバイス"
}}

営業担当の発言: {user_input}
顧客ペルソナ: {customer_context}"""

# --- Page Setup ---
st.set_page_config(
    layout="wide",
    page_title="GWS Agent Sales Dojo",
    page_icon="🧩"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 10px; padding: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .review-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-left: 5px solid #4CAF50;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .review-box-warning {
        background-color: #fff3cd;
        padding: 20px;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .review-box-danger {
        background-color: #f8d7da;
        padding: 20px;
        border-left: 5px solid #dc3545;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-mid { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .persona-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .header-subtitle {
        color: #6c757d;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "review_log" not in st.session_state:
    st.session_state.review_log = []
if "simulation_active" not in st.session_state:
    st.session_state.simulation_active = False
if "customer_persona" not in st.session_state:
    st.session_state.customer_persona = {}
if "trust_level" not in st.session_state:
    st.session_state.trust_level = 0
if "llm_mode" not in st.session_state:
    st.session_state.llm_mode = "mock"

# --- LLM Client Setup ---
def get_anthropic_client() -> Optional[anthropic.Anthropic]:
    """Initialize Anthropic client if API key is available."""
    # Try Streamlit secrets first (for Streamlit Cloud), then env var
    api_key = None
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        pass

    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key and ANTHROPIC_AVAILABLE:
        return anthropic.Anthropic(api_key=api_key)
    return None

def call_llm(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """Call LLM API or return mock response."""
    client = get_anthropic_client()

    if client and st.session_state.llm_mode == "api":
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )
            return response.content[0].text
        except Exception as e:
            st.warning(f"API呼び出しエラー: {e}。モックモードに切り替えます。")
            st.session_state.llm_mode = "mock"

    return None  # Return None to indicate mock mode should be used

# --- Helper Functions ---

def init_persona():
    """Initialize a new customer persona."""
    industry = random.choice(INDUSTRIES)
    position = random.choice(POSITIONS)
    budget = random.choice(BUDGETS)
    personality = random.choice(PERSONALITIES)

    st.session_state.customer_persona = {
        "industry": industry,
        "position": position,
        "budget": budget,
        "pain_point": f"{industry}特有のアナログ業務（FAX/電話/手入力）によるボトルネック",
        "personality": personality
    }
    st.session_state.messages = []
    st.session_state.review_log = []
    st.session_state.simulation_active = True
    st.session_state.trust_level = 0

    # Initial Greeting from Customer
    initial_msg = generate_initial_greeting()
    st.session_state.messages.append({"role": "assistant", "content": initial_msg})

def generate_initial_greeting() -> str:
    """Generate customer's initial greeting."""
    persona = st.session_state.customer_persona

    system_prompt = CUSTOMER_SYSTEM_PROMPT.format(**persona)
    user_msg = "商談を開始してください。自己紹介と課題の説明をしてください。"

    llm_response = call_llm(system_prompt, user_msg)

    if llm_response:
        return llm_response

    # Mock response
    return f"""初めまして。{persona['industry']}企業の{persona['position']}をしております。

当社では『{persona['pain_point']}』という課題を抱えております。貴社のAIエージェントソリューションで解決できると伺いましたが、具体的にどのような仕組みなのでしょうか？

予算は{persona['budget']}程度を想定しておりますが、この範囲で実現可能でしょうか。"""

def generate_manager_feedback(user_input: str, customer_context: Dict) -> Dict:
    """Generate Manager Agent's feedback on the sales rep's input."""

    system_prompt = MANAGER_SYSTEM_PROMPT.format(
        user_input=user_input,
        customer_context=str(customer_context)
    )

    llm_response = call_llm(system_prompt, f"以下の営業発言を評価してください：\n{user_input}")

    if llm_response:
        try:
            import json
            # Try to extract JSON from the response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                result = json.loads(llm_response[json_start:json_end])
                return result
        except (json.JSONDecodeError, KeyError):
            pass

    # === Enhanced Mock Evaluation Logic ===
    feedback_points = []
    penalties = []
    breakdown = {
        "micro_agent": 0,
        "state_management": 0,
        "organic_looping": 0,
        "human_in_loop": 0
    }

    # --- NEGATIVE PATTERNS (Dangerous proposals) ---
    danger_patterns = [
        ("全部自動", "『全部自動化』は危険な提案です。例外処理やエラー時の対応が考慮されていません。"),
        ("全自動", "『全自動』という表現は顧客に不信感を与えます。人間の介入ポイントを明示してください。"),
        ("工数ゼロ", "『工数ゼロ』は非現実的です。適切な期待値設定が必要です。"),
        ("何でもできる", "『何でもできる』は思考停止した提案です。具体的な役割分担を示してください。"),
        ("魔法", "『魔法のように』という表現は避けてください。技術的な根拠を示しましょう。"),
        ("簡単に導入", "導入の容易さだけでなく、運用フェーズの設計も説明してください。"),
    ]

    penalty_score = 0
    for pattern, warning in danger_patterns:
        if pattern in user_input:
            penalties.append(f"🚨 {warning}")
            penalty_score += 15

    # --- POSITIVE PATTERNS with Context ---

    # Micro-Agent Strategy (30 points)
    micro_score = 0
    # High value: Specific role definition
    if any(x in user_input for x in ["解析Gem", "作成Gem", "通知Gem", "判定Gem", "リマインドGem"]):
        micro_score += 20
        feedback_points.append("✅ 具体的なGemの役割定義あり - Micro-Agent戦略の理想形")
    elif "役割" in user_input and any(x in user_input for x in ["分け", "分割", "細分化", "分離"]):
        micro_score += 15
        feedback_points.append("✅ 役割分割の概念を説明 - Micro-Agent戦略")
    elif any(x in user_input for x in ["単一責任", "専門特化", "それぞれの"]):
        micro_score += 12
        feedback_points.append("✅ 単一責任の原則への言及あり")
    elif any(x in user_input for x in ["Gem", "エージェント"]) and "連携" in user_input:
        micro_score += 10
        feedback_points.append("✅ エージェント連携の概念あり")
    elif any(x in user_input for x in ["Gem", "エージェント"]):
        micro_score += 5
        feedback_points.append("⚠️ Gem/エージェントの言及はあるが、具体的な役割定義が不足")

    breakdown["micro_agent"] = min(micro_score, 30)

    # State Management (25 points)
    state_score = 0
    if any(x in user_input for x in ["リルート", "フォールバック", "代替ルート"]):
        state_score += 15
        feedback_points.append("✅ エラー時のリルート設計あり - 動的ステート管理")
    if any(x in user_input for x in ["例外", "エラー"]) and any(x in user_input for x in ["処理", "対応", "時"]):
        state_score += 10
        feedback_points.append("✅ 例外処理への言及あり")
    if any(x in user_input for x in ["3日", "期限", "タイムアウト", "返信がない"]):
        state_score += 8
        feedback_points.append("✅ 時間ベースのトリガー設計あり")

    breakdown["state_management"] = min(state_score, 25)

    # Organic Looping (25 points)
    loop_score = 0
    if "循環" in user_input and any(x in user_input for x in ["構造", "設計", "組み"]):
        loop_score += 20
        feedback_points.append("✅ 循環構造の設計を明示 - 有機的循環の理想形")
    elif any(x in user_input for x in ["ループ", "繰り返し", "定期的"]):
        loop_score += 12
        feedback_points.append("✅ ループ処理の概念あり")
    if "連携" in user_input and any(x in user_input for x in ["次に", "その後", "まず"]):
        loop_score += 8
        feedback_points.append("✅ 処理フローの順序を説明")
    if any(x in user_input for x in ["取りこぼし", "漏れ", "フォローアップ"]):
        loop_score += 5
        feedback_points.append("✅ 取りこぼし防止の意識あり")

    breakdown["organic_looping"] = min(loop_score, 25)

    # Human-in-the-Loop (20 points)
    human_score = 0
    if ("人間" in user_input or "担当者" in user_input) and any(x in user_input for x in ["承認", "確認", "判断"]):
        human_score += 15
        feedback_points.append("✅ 人間による承認フローを明示 - Human-in-the-Loop")
    elif "Human-in-the-Loop" in user_input or "ヒューマンインザループ" in user_input:
        human_score += 12
        feedback_points.append("✅ Human-in-the-Loop概念への直接言及")
    elif any(x in user_input for x in ["承認ボタン", "最終確認", "ゲートキーパー"]):
        human_score += 15
        feedback_points.append("✅ 具体的な承認UIの言及あり")
    elif any(x in user_input for x in ["承認", "確認", "レビュー"]):
        human_score += 8
        feedback_points.append("✅ 確認プロセスへの言及あり")

    breakdown["human_in_loop"] = min(human_score, 20)

    # --- BONUS: Security & ROI ---
    bonus_score = 0
    if any(x in user_input for x in ["匿名化", "マスキング", "個人情報"]):
        bonus_score += 5
        feedback_points.append("🛡️ セキュリティ対策（匿名化）への言及 - 信頼性向上")
    if any(x in user_input for x in ["学習に使われない", "学習除外", "データ保護"]):
        bonus_score += 5
        feedback_points.append("🛡️ データ学習除外への言及 - 顧客の懸念に対応")

    # === STRATEGY: Beachhead Strategy (営業戦略点) ===
    strategy_score = 0
    strategy_feedback = []

    # Scope Down (範囲限定) - 15点
    scope_keywords = ["特定業務", "絞って", "だけ", "のみ", "一部", "請求書", "日程調整", "採用", "問い合わせ"]
    if any(x in user_input for x in ["まずは", "特定", "絞"]) and any(x in user_input for x in scope_keywords):
        strategy_score += 15
        strategy_feedback.append("📉 【Scope Down】対象範囲を限定した提案 - 全失注リスクを回避")

    # Budget Fit (予算適合) - 10点: 部長決裁ライン（<500万）を意識
    price_keywords = ["100万", "200万", "300万", "百万", "数百万", "トライアル", "PoC"]
    if any(x in user_input for x in price_keywords):
        strategy_score += 10
        strategy_feedback.append("📉 【Budget Fit】部長決裁ライン（300万以下）を意識した金額提示")

    # Cost Down ROI (短期ROI) - 10点
    if any(x in user_input for x in ["時間", "工数", "削減"]) and any(x in user_input for x in ["月", "週", "日", "3ヶ月", "半年"]):
        strategy_score += 10
        strategy_feedback.append("📉 【Quick ROI】短期的な効果を数字で提示 - 稟議を通しやすい")

    # Scalability (拡張性への言及) - 5点
    if any(x in user_input for x in ["成功したら", "次は", "第一フェーズ", "フェーズ1", "将来的", "拡張"]):
        strategy_score += 5
        strategy_feedback.append("📉 【Scalability】将来の全体導入への布石を提示")

    # スモールスタート + 金額の組み合わせ = 高評価
    if any(x in user_input for x in ["スモールスタート", "PoC", "実証", "パイロット", "トライアル"]):
        if any(x in user_input for x in price_keywords):
            strategy_score += 10
            strategy_feedback.append("🎯 【Beachhead Strategy】小さく始めて成功を積む - 理想的な着地点戦略")
        else:
            strategy_score += 5
            strategy_feedback.append("⚠️ スモールスタートは良いが、具体的な金額感（100-300万）を提示すると説得力が増します")

    # BAD: 単なる値引き（機能を削らない安売り）
    if any(x in user_input for x in ["値下げ", "割引", "安く"]):
        if not any(x in user_input for x in ["絞", "限定", "特定", "だけ"]):
            strategy_score -= 15
            strategy_feedback.append("🚫 【Bad Move】機能を削らず値引きだけで解決しようとしています。『範囲を絞ってコストを下げる』が正解です。")

    # Calculate final score (技術点 + 戦略点)
    base_score = sum(breakdown.values()) + bonus_score
    tech_score = max(0, base_score - penalty_score)
    total_score = tech_score + strategy_score
    final_score = min(total_score, 100)

    # Combine feedback
    all_feedback = penalties + feedback_points + strategy_feedback

    # --- Generate Improvement Advice ---
    improvement = ""
    if penalty_score > 0:
        improvement = "危険なキーワードを避け、具体的なアーキテクチャ（Gem分割、承認フロー、循環構造）を説明してください。"
    elif final_score < 30:
        all_feedback.append("⚠️ 設計哲学（Micro-Agent、有機的循環など）への言及が不足しています。")
        improvement = "単なる機能説明ではなく、Gemの役割分割、承認フロー、循環構造を具体的に説明してください。"
    elif final_score < 50:
        improvement = "用語は使えていますが、具体的なInput/Output（I-P-O）の説明が不足しています。どのデータがトリガーになり、どう処理されるか明示してください。"
    elif final_score < 70:
        improvement = "良い提案です。さらに顧客の業界特有の課題に当てはめた具体例を追加すると説得力が増します。"
    elif final_score >= 70:
        all_feedback.append("🎯 設計哲学を適切に伝えられています。")
        improvement = "素晴らしい提案です。この調子で顧客の懸念（セキュリティ、予算）にも先回りして対応しましょう。"

    if final_score >= 90:
        all_feedback.append("🏆 完璧です！Micro-Agent、Dynamic State、Organic Loopingの3要素が網羅されています。")

    # Length check
    if len(user_input) < 30:
        all_feedback.insert(0, "⚠️ 説明が短すぎます。詳細なアーキテクチャ説明が必要です。")
        final_score = min(final_score, 20)
        improvement = "顧客の不安を払拭するため、具体的な仕組みを説明してください。"

    return {
        "score": final_score,
        "tech_score": tech_score,
        "strategy_score": max(0, strategy_score),
        "breakdown": breakdown,
        "feedback": all_feedback if all_feedback else ["⚠️ 評価ポイントとなるキーワードが見つかりませんでした。"],
        "improvement": improvement or "設計哲学に基づいた説明を心がけてください。"
    }

def generate_customer_response(user_input: str, context: Dict) -> str:
    """Generate Customer Agent's response."""

    system_prompt = CUSTOMER_SYSTEM_PROMPT.format(**context)

    # Include conversation history for context
    history = "\n".join([
        f"{'営業' if m['role'] == 'user' else '顧客'}: {m['content']}"
        for m in st.session_state.messages[-6:]  # Last 3 exchanges
    ])

    user_msg = f"""これまでの会話:
{history}

営業の最新発言: {user_input}

上記に対して、ペルソナとして応答してください。"""

    llm_response = call_llm(system_prompt, user_msg)

    if llm_response:
        # Update trust level based on response tone
        if "面白い" in llm_response or "興味深い" in llm_response:
            st.session_state.trust_level = min(st.session_state.trust_level + 15, 100)
        elif "不安" in llm_response or "心配" in llm_response:
            st.session_state.trust_level = max(st.session_state.trust_level - 5, 0)
        return llm_response

    # Mock responses based on trust level and keywords
    trust = st.session_state.trust_level

    # Check for good keywords to increase trust
    good_keywords = ["エージェント", "Gem", "循環", "ループ", "人間", "承認", "連携"]
    keyword_hits = sum(1 for kw in good_keywords if kw in user_input)
    st.session_state.trust_level = min(trust + keyword_hits * 10, 100)

    # === Beachhead Strategy: スモールスタート提案への軟化ロジック ===
    compromise_keywords = ["スモールスタート", "PoC", "トライアル", "まずは", "絞って", "特定業務", "だけ"]
    price_keywords = ["100万", "200万", "300万", "百万"]

    has_compromise = any(kw in user_input for kw in compromise_keywords)
    has_price = any(kw in user_input for kw in price_keywords)

    if has_compromise and has_price:
        # スモールスタート + 金額提示 → 大幅に信頼度UP & 特別な応答
        st.session_state.trust_level = min(st.session_state.trust_level + 30, 100)
        return f"""...{context['budget'].split('（')[0]}の範囲内ですね。それなら私の決裁で進められます。

特定の業務に絞って、まず成果を見てみる形なら現実的ですね。{context['industry']}では特に{'請求書処理' if context['industry'] in ['製造業', '物流', '小売'] else '問い合わせ対応'}がボトルネックなので、そこからお願いできますか？

3ヶ月後に効果を測定して、良ければ次のフェーズに進みましょう。"""

    elif has_compromise:
        # スモールスタート提案あり（金額なし）→ 前向きだが金額確認
        st.session_state.trust_level = min(st.session_state.trust_level + 15, 100)
        return f"""なるほど、小さく始めるというのは賢明ですね。

具体的にどのくらいの予算感で、どの業務から始めることを想定されていますか？{context['budget']}の範囲内なら、私の判断で進められます。"""

    if trust < 20:
        responses = [
            "なるほど。しかし、従来のRPAと何が違うのですか？単線的な自動化では例外処理で止まってしまうのが悩みです。",
            "興味深いですが、具体的にどのような仕組みで動くのでしょうか？「AIで自動化」という説明だけでは判断できません。",
            f"当社は{context['industry']}ですが、業界特有の要件に対応できるのでしょうか？"
        ]
    elif trust < 50:
        responses = [
            "なるほど、個別の専門エージェントが連携するという考え方は面白いですね。ただ、管理が煩雑になりませんか？",
            "セキュリティ面が心配です。社内データが学習に使われたり、外部に漏れたりすることはありませんか？",
            "具体的なアウトプットイメージが湧きにくいです。Google Workspace上でどう動くのか、デモを見せていただけますか？"
        ]
    elif trust < 80:
        responses = [
            f"かなり理解が深まりました。{context['budget']}の範囲で、まずはPoC（概念実証）から始めることは可能でしょうか？",
            "導入に際して、現場への説明や研修はどのようにサポートいただけますか？",
            "他社での導入事例があれば教えていただけますか？特に{context['industry']}での実績は？"
        ]
    else:
        responses = [
            "詳しいご説明ありがとうございます。前向きに検討したいと思います。次のステップとして何を準備すればよいでしょうか？",
            "社内で稟議を上げるために、提案書をいただくことは可能でしょうか？",
            "ぜひ上層部にも説明いただきたいのですが、プレゼンの機会を設けられますか？"
        ]

    return random.choice(responses)

def generate_final_report() -> Dict:
    """Generate a comprehensive session report."""
    if not st.session_state.review_log:
        return None

    total_turns = len(st.session_state.review_log)
    avg_score = sum(log['feedback']['score'] for log in st.session_state.review_log) / total_turns

    # Aggregate breakdown scores
    avg_breakdown = {
        "micro_agent": 0,
        "state_management": 0,
        "organic_looping": 0,
        "human_in_loop": 0
    }

    for log in st.session_state.review_log:
        if 'breakdown' in log['feedback']:
            for key in avg_breakdown:
                avg_breakdown[key] += log['feedback']['breakdown'].get(key, 0)

    for key in avg_breakdown:
        avg_breakdown[key] = round(avg_breakdown[key] / total_turns, 1)

    # Identify strengths and weaknesses
    max_key = max(avg_breakdown, key=avg_breakdown.get)
    min_key = min(avg_breakdown, key=avg_breakdown.get)

    category_names = {
        "micro_agent": "Micro-Agent Strategy",
        "state_management": "動的ステート管理",
        "organic_looping": "有機的循環",
        "human_in_loop": "Human-in-the-Loop"
    }

    return {
        "total_turns": total_turns,
        "avg_score": round(avg_score, 1),
        "final_trust": st.session_state.trust_level,
        "avg_breakdown": avg_breakdown,
        "strength": category_names[max_key],
        "weakness": category_names[min_key],
        "recommendation": get_recommendation(avg_score, st.session_state.trust_level)
    }

def get_recommendation(avg_score: float, trust_level: int) -> str:
    """Generate personalized recommendation based on performance."""
    if avg_score >= 70 and trust_level >= 70:
        return "素晴らしいパフォーマンスです！設計哲学を効果的に伝え、顧客の信頼を獲得できています。"
    elif avg_score >= 50 and trust_level >= 50:
        return "良い傾向です。より具体的な事例や数字を交えることで、説得力を高められます。"
    elif avg_score >= 50:
        return "技術説明は適切ですが、顧客のペルソナに合わせたカスタマイズが必要です。"
    elif trust_level >= 50:
        return "顧客との関係構築は良好ですが、設計哲学の説明をより強化してください。"
    else:
        return "Micro-Agent戦略、有機的循環、Human-in-the-Loopの概念を意識した説明を心がけてください。"

def get_score_class(score: int) -> str:
    """Return CSS class based on score."""
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-mid"
    return "score-low"

def get_review_box_class(score: int) -> str:
    """Return CSS class for review box based on score."""
    if score >= 70:
        return "review-box"
    elif score >= 40:
        return "review-box-warning"
    return "review-box-danger"

# --- UI Layout ---

st.title("🧩 GWS Agent Architecture Sales Dojo")
st.markdown('<p class="header-subtitle">Powered by Business Ecosystem Grand Architect</p>', unsafe_allow_html=True)

# Sidebar for Settings
with st.sidebar:
    st.header("⚙️ Settings")

    # LLM Mode Toggle
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and ANTHROPIC_AVAILABLE:
        mode = st.radio(
            "LLM Mode",
            ["api", "mock"],
            format_func=lambda x: "🤖 API Mode (Claude)" if x == "api" else "🎭 Mock Mode",
            index=0 if st.session_state.llm_mode == "api" else 1
        )
        st.session_state.llm_mode = mode
    else:
        st.info("💡 ANTHROPIC_API_KEYを.envに設定するとAPI Modeが使用可能になります")
        st.session_state.llm_mode = "mock"

    st.markdown("---")
    st.header("🎯 Scenario Setup")

    if st.button("🔄 新しいシナリオを生成", type="primary"):
        init_persona()
        st.rerun()

    if st.session_state.simulation_active:
        st.markdown(f"""
        <div class="persona-card">
            <h4>👤 顧客ペルソナ</h4>
            <p><strong>業界:</strong> {st.session_state.customer_persona['industry']}</p>
            <p><strong>役職:</strong> {st.session_state.customer_persona['position']}</p>
            <p><strong>予算:</strong> {st.session_state.customer_persona['budget']}</p>
            <p><strong>性格:</strong> {st.session_state.customer_persona['personality'][:30]}...</p>
        </div>
        """, unsafe_allow_html=True)

        # Trust Level Indicator
        st.metric("💝 信頼度", f"{st.session_state.trust_level}%")
        st.progress(st.session_state.trust_level / 100)

    st.markdown("---")
    st.markdown("""
    **📋 技術点 (100点満点):**
    - Micro-Agent Strategy (30点)
    - 動的ステート管理 (25点)
    - 有機的循環 (25点)
    - Human-in-the-Loop (20点)

    **📉 戦略点 (ボーナス):**
    - Scope Down (範囲限定)
    - Budget Fit (予算適合)
    - Quick ROI (短期効果)
    - Scalability (拡張性)
    """)

# Main Interface
if not st.session_state.simulation_active:
    st.markdown("""
    ## 👋 ようこそ Sales Dojoへ

    このシミュレーターでは、**GWS Agent Architecture**の営業スキルを磨くことができます。

    ### 🎯 トレーニングの目的
    - **Micro-Agent Strategy**: 単一責任の原則に基づく設計思想を伝える
    - **動的ステート管理**: エラー処理やリルートの仕組みを説明する
    - **有機的循環**: エージェント間の連携を具体的に示す
    - **Human-in-the-Loop**: 人間の介入ポイントを明確にする

    ### 🚀 始め方
    👈 左側のサイドバーから **「新しいシナリオを生成」** をクリックしてください。

    ランダムに生成された顧客ペルソナに対して、営業トークを実践できます。
    """)
else:
    col_chat, col_review = st.columns([2, 1])

    # Left Column: Chat Interface
    with col_chat:
        st.subheader("💬 商談ルーム")

        # Display Chat History
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "assistant" else "👔"):
                    st.markdown(msg["content"])

        # User Input (Text + Voice)
        input_col1, input_col2 = st.columns([6, 1])

        # Initialize audio tracking in session state
        if "last_audio_hash" not in st.session_state:
            st.session_state.last_audio_hash = None

        with input_col2:
            if AUDIO_AVAILABLE:
                st.markdown("**🎤 音声**")
                audio_bytes = audio_recorder(
                    text="",
                    recording_color="#e74c3c",
                    neutral_color="#667eea",
                    icon_size="2x",
                    pause_threshold=2.0,
                    key="audio_recorder"
                )
            else:
                audio_bytes = None

        # Process voice input (only if new audio)
        voice_text = None
        if audio_bytes and AUDIO_AVAILABLE:
            # Create hash to detect if this is new audio
            audio_hash = hash(audio_bytes)
            if audio_hash != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_hash
                with st.spinner("音声を認識中..."):
                    voice_text = transcribe_audio(audio_bytes)
                    if voice_text:
                        st.success(f"認識結果: {voice_text}")

        with input_col1:
            prompt = st.chat_input("顧客への提案を入力してください...")

        # Use voice text if available, otherwise use typed text
        final_prompt = voice_text if voice_text else prompt

        if final_prompt:
            # 1. Add User Message
            st.session_state.messages.append({"role": "user", "content": final_prompt})

            # 2. Generate Manager Feedback (Parallel Process)
            feedback = generate_manager_feedback(final_prompt, st.session_state.customer_persona)
            st.session_state.review_log.append({
                "turn": len(st.session_state.messages) // 2,
                "user_input": final_prompt,
                "feedback": feedback
            })

            # 3. Generate Customer Response
            with st.spinner(f"{st.session_state.customer_persona['position']} が検討中..."):
                time.sleep(0.5 if st.session_state.llm_mode == "api" else 1)
                response = generate_customer_response(final_prompt, st.session_state.customer_persona)
                st.session_state.messages.append({"role": "assistant", "content": response})

            st.rerun()

    # Right Column: Manager Review
    with col_review:
        st.subheader("📊 マネージャー評価")

        if st.session_state.review_log:
            last_review = st.session_state.review_log[-1]
            score = last_review['feedback']['score']

            # Score Card with color
            score_class = get_score_class(score)
            st.markdown(f"""
            <div class="metric-card">
                <h2 class="{score_class}">{score}/100</h2>
                <p>最新ターンスコア</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Breakdown (if available)
            if 'breakdown' in last_review['feedback']:
                bd = last_review['feedback']['breakdown']
                cols = st.columns(2)
                cols[0].metric("Micro-Agent", f"{bd['micro_agent']}/30")
                cols[1].metric("State Mgmt", f"{bd['state_management']}/25")
                cols = st.columns(2)
                cols[0].metric("Organic Loop", f"{bd['organic_looping']}/25")
                cols[1].metric("Human-in-Loop", f"{bd['human_in_loop']}/20")

            # Strategy Score Indicator (営業戦略点)
            st.markdown("---")
            st.markdown("**📉 Cost/Scope Logic**")
            tech_score = last_review['feedback'].get('tech_score', score)
            strategy_score = last_review['feedback'].get('strategy_score', 0)

            strat_cols = st.columns(2)
            strat_cols[0].metric("技術点", f"{tech_score}")
            strat_cols[1].metric("戦略点", f"{strategy_score}", delta=f"+{strategy_score}" if strategy_score > 0 else None)

            if strategy_score >= 20:
                st.success("🎯 **Beachhead Strategy成功** - 小さく始めて勝ちパターンを作る提案")
            elif strategy_score > 0:
                st.warning("📉 スモールスタートの兆候あり - 具体的な金額を提示するとさらに効果的")

            # Feedback Box
            review_box_class = get_review_box_class(score)
            feedback_html = "<br>".join(last_review['feedback']['feedback'])
            st.markdown(f"""
            <div class="{review_box_class}">
                <strong>Turn {last_review['turn']} フィードバック:</strong><br><br>
                {feedback_html}
            </div>
            """, unsafe_allow_html=True)

            if 'improvement' in last_review['feedback'] and last_review['feedback']['improvement']:
                st.info(f"💡 **改善ポイント:** {last_review['feedback']['improvement']}")

            st.markdown("---")

            # History Log
            with st.expander("📝 過去の評価履歴", expanded=False):
                for log in reversed(st.session_state.review_log[:-1]):
                    st.markdown(f"**Turn {log['turn']}** (Score: {log['feedback']['score']})")
                    st.caption(f"発言: {log['user_input'][:50]}...")
                    st.markdown("---")
        else:
            st.info("商談を開始してください。あなたの発言に対してリアルタイムで評価を行います。")

        # End Session Button
        st.markdown("---")
        if st.button("🏁 セッション終了 & レポート生成", type="secondary"):
            report = generate_final_report()
            if report:
                st.session_state.simulation_active = False
                st.session_state.final_report = report
                st.rerun()

# Final Report Display
if not st.session_state.simulation_active and "final_report" in st.session_state:
    report = st.session_state.final_report

    st.markdown("---")
    st.header("📊 セッションレポート")

    col1, col2, col3 = st.columns(3)
    col1.metric("総ターン数", report["total_turns"])
    col2.metric("平均スコア", f"{report['avg_score']}/100")
    col3.metric("最終信頼度", f"{report['final_trust']}%")

    st.markdown("### 📈 カテゴリ別平均スコア")
    cols = st.columns(4)
    cols[0].metric("Micro-Agent", f"{report['avg_breakdown']['micro_agent']}/30")
    cols[1].metric("State Mgmt", f"{report['avg_breakdown']['state_management']}/25")
    cols[2].metric("Organic Loop", f"{report['avg_breakdown']['organic_looping']}/25")
    cols[3].metric("Human-in-Loop", f"{report['avg_breakdown']['human_in_loop']}/20")

    st.markdown("### 💪 強み・弱み分析")
    st.success(f"**強み:** {report['strength']}")
    st.warning(f"**改善点:** {report['weakness']}")

    st.markdown("### 💡 総評")
    st.info(report['recommendation'])

    if st.button("🔄 新しいセッションを開始"):
        del st.session_state.final_report
        init_persona()
        st.rerun()

# Footer
st.markdown("---")
st.caption("🧩 GWS Agent Architecture Sales Dojo | Built with Streamlit & Claude API")
