"""
Scenario Runner - Automated Role-Play Logic Testing for Sales Dojo
===================================================================
Powered by Business Ecosystem Grand Architect

This script validates business logic by running predefined sales scenarios
and checking if the system responds correctly to:
- Golden Path (perfect SPIN progression)
- Bad Actor (stage skipping, premature closing)
- Pivot scenarios (budget objection handling)

Requires: pip install playwright && playwright install
"""

import sys
import io
import time
import json
from dataclasses import dataclass
from typing import List, Optional

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

# --- Configuration ---
TARGET_URL = "https://sales-dojo.onrender.com/"  # Change to localhost for local testing
HEADLESS = False  # Set True for CI/CD
WAIT_AFTER_INPUT = 5  # Seconds to wait after each input (increased for Render)


@dataclass
class Turn:
    """A single turn in a conversation scenario"""
    input_text: str
    expected_stage_keyword: str  # Expected stage name should contain this
    expected_status: str         # "Good", "Alert", "Loop", "Demo"
    min_score: int              # Minimum acceptable score
    max_score: Optional[int] = None  # Maximum score (for Alert cases)


@dataclass
class Scenario:
    """A complete test scenario with multiple turns"""
    name: str
    description: str
    turns: List[Turn]


# --- Test Scenarios Definition ---

# Scenario 1: The Golden Path - Perfect SPIN Progression
SCENARIO_GOLDEN = Scenario(
    name="The Golden Path",
    description="Perfect SPIN progression from Opening to Closing",
    turns=[
        Turn(
            "初めまして。貴社の業界では人手不足が課題と伺っていますが、現状はいかがですか？",
            "SITUATION", "Good", 40  # Adjusted: basic question without strategy keywords
        ),
        Turn(
            "なるほど。具体的に、請求書処理には何名くらいの人数で、どのくらい時間をかけていますか？",
            "SITUATION", "Good", 40
        ),
        Turn(
            "それは多いですね。入力ミスや確認漏れなどの課題は発生していませんか？",
            "PROBLEM", "Good", 40
        ),
        Turn(
            "ミスが発生すると、再発行の手間や取引先への信用問題など、深刻な影響やリスクがありますよね？",
            "IMPLICATION", "Good", 40
        ),
        Turn(
            "もしGemエージェントが自動で承認フローを回し、担当者は承認ボタンを押すだけになれば、そのリスクはゼロになりますがいかがですか？",
            "NEED_PAYOFF", "Good", 50  # Contains "gem", "エージェント", "承認"
        ),
        Turn(
            "まずは300万円のPoCでスモールスタートして、トライアルとして効果を検証しませんか？",
            "CLOSING", "Good", 55  # Contains strategy keywords
        )
    ]
)

# Scenario 2: The Premature Closer - Stage Skipping
SCENARIO_RUSHER = Scenario(
    name="The Premature Closer",
    description="Skips stages and jumps to closing immediately - should trigger Alert",
    turns=[
        Turn(
            "初めまして。よろしくお願いします。",
            "OPENING", "Good", 30
        ),
        Turn(
            "当社のAIエージェントGemは最高です。今すぐ契約して導入しましょう！金額は500万円です。",
            "OPENING", "Alert", 0, 50  # Should NOT progress, Alert status, low score
        ),
        Turn(
            "安くしますよ？今すぐ契約してください。トライアルも可能です。",
            "OPENING", "Alert", 0, 50  # Still stuck at OPENING with Alert
        )
    ]
)

# Scenario 3: The Pivot - Handling Budget Objection with Small Start
SCENARIO_PIVOT = Scenario(
    name="The Pivot Master",
    description="Handles budget objection by pivoting to small start proposal",
    turns=[
        Turn(
            "御社の現状について教えてください。どのような業務に人手がかかっていますか？",
            "SITUATION", "Good", 40  # Basic SITUATION question
        ),
        Turn(
            "その業務でミスや課題が発生することはありますか？",
            "PROBLEM", "Good", 40  # Basic PROBLEM question
        ),
        Turn(
            # Avoid "フロー" (SITUATION keyword) - use "提案" and "エージェント" for NEED_PAYOFF
            "Gemエージェントを提案します。AIが自動で処理を行い、300万円でスモールスタートできます。",
            "NEED_PAYOFF", "Good", 50  # Contains "提案", "gem", "エージェント", "ai"
        )
    ]
)

# Scenario 4: The Loop Back - Unnecessary Repetition
SCENARIO_LOOPER = Scenario(
    name="The Loop Back",
    description="Goes back to earlier stages unnecessarily - should trigger Loop status",
    turns=[
        Turn(
            "現状について教えてください。どのような業務がありますか？",
            "SITUATION", "Good", 40  # Basic SITUATION question
        ),
        Turn(
            "その業務で課題やミスは発生していますか？",
            "PROBLEM", "Good", 40  # Basic PROBLEM question
        ),
        Turn(
            "ところで、御社の現状をもう一度確認させてください。何人くらいで作業していますか？",
            "PROBLEM", "Loop", 20  # Loop back detection - lower score expected
        )
    ]
)


# --- Test Runner Engine ---

def get_debug_info(page) -> dict:
    """Extract debug information from the hidden DOM element"""
    try:
        debug_el = page.locator("#test-debug-info")
        if debug_el.count() > 0:
            return {
                "stage": debug_el.get_attribute("data-stage") or "Unknown",
                "score": float(debug_el.get_attribute("data-last-score") or 0),
                "status": debug_el.get_attribute("data-last-status") or "None",
                "detected_stage": debug_el.get_attribute("data-detected-stage") or "Unknown",
                "next_stage": debug_el.get_attribute("data-next-stage") or "Unknown",
                "turn_count": int(debug_el.get_attribute("data-turn-count") or 0),
                "render_time": debug_el.get_attribute("data-render-time") or "0",
                "simulation_active": debug_el.get_attribute("data-simulation-active") == "True",
                "demo_mode": debug_el.get_attribute("data-demo-mode") == "True"
            }
    except Exception as e:
        print(f"      ⚠️ Could not read debug info: {e}")

    return {"stage": "Unknown", "score": 0, "status": "None", "detected_stage": "Unknown", "next_stage": "Unknown", "turn_count": 0, "render_time": "0", "simulation_active": False, "demo_mode": False}


def initialize_scenario(page):
    """Start a new scenario and ensure proper state"""
    print("   🔄 Initializing scenario...")

    # Try to start new scenario
    for btn_text in ["新規シナリオ開始", "リセット", "開始"]:
        btn = page.locator(f'button:has-text("{btn_text}")')
        if btn.count() > 0:
            btn.first.click()
            time.sleep(3)
            print(f"   ✅ Clicked: {btn_text}")
            break

    # Ensure demo mode is OFF
    debug_info = get_debug_info(page)
    if debug_info.get("demo_mode"):
        demo_labels = page.locator('label:has-text("デモ")')
        if demo_labels.count() > 0:
            demo_labels.first.click()
            time.sleep(1)
            print("   ✅ Demo mode disabled")

    return get_debug_info(page)


def find_chat_input(page):
    """Find the chat input element with multiple fallback selectors"""
    # Try textarea first (Streamlit chat input is typically a textarea)
    selectors = [
        'textarea[data-testid="stChatInputTextArea"]',
        'textarea',  # Generic textarea
        'input[placeholder*="提案"]',
        'input[placeholder*="入力"]',
    ]

    for selector in selectors:
        try:
            el = page.locator(selector)
            if el.count() > 0:
                for i in range(el.count()):
                    elem = el.nth(i)
                    if elem.is_visible():
                        return elem
        except:
            pass

    # Try placeholder-based search with partial match
    placeholders = [
        "提案を入力してください",
        "提案を入力",
        "入力してください",
        "入力"
    ]
    for placeholder in placeholders:
        try:
            el = page.get_by_placeholder(placeholder, exact=False)
            if el.count() > 0 and el.first.is_visible():
                return el.first
        except:
            pass

    # Last resort: find any visible input/textarea in the chat area
    try:
        chat_container = page.locator('[data-testid="stChatInput"]')
        if chat_container.count() > 0:
            textarea = chat_container.locator('textarea')
            if textarea.count() > 0 and textarea.first.is_visible():
                return textarea.first
    except:
        pass

    return None


def run_scenario(page, scenario: Scenario) -> dict:
    """Run a single scenario and return results"""
    print(f"\n{'='*60}")
    print(f"🎬 Scenario: {scenario.name}")
    print(f"   {scenario.description}")
    print('='*60)

    # Initialize
    initialize_scenario(page)
    time.sleep(2)

    results = {
        "name": scenario.name,
        "passed": True,
        "turns": [],
        "errors": []
    }

    for i, turn in enumerate(scenario.turns):
        print(f"\n   🔹 Turn {i+1}/{len(scenario.turns)}")
        print(f"      Input: \"{turn.input_text[:50]}...\"")
        print(f"      Expected: Stage={turn.expected_stage_keyword}, Status={turn.expected_status}, Score>={turn.min_score}")

        turn_result = {
            "turn": i + 1,
            "input": turn.input_text[:50],
            "expected": {"stage": turn.expected_stage_keyword, "status": turn.expected_status, "min_score": turn.min_score},
            "actual": {},
            "passed": True,
            "errors": []
        }

        try:
            # Find and fill chat input
            chat_input = find_chat_input(page)

            if not chat_input:
                error = "Chat input not found - Demo mode may be ON"
                print(f"      ❌ {error}")
                turn_result["errors"].append(error)
                turn_result["passed"] = False
                results["errors"].append(f"Turn {i+1}: {error}")

                # Try to disable demo mode and retry
                debug_info = get_debug_info(page)
                if debug_info.get("demo_mode"):
                    demo_labels = page.locator('label:has-text("デモ")')
                    if demo_labels.count() > 0:
                        demo_labels.first.click()
                        time.sleep(2)
                        chat_input = find_chat_input(page)

                if not chat_input:
                    results["turns"].append(turn_result)
                    continue

            # Get turn count before submitting
            pre_debug = get_debug_info(page)
            pre_turn_count = pre_debug.get("turn_count", 0)

            # Submit input
            chat_input.fill(turn.input_text)
            chat_input.press("Enter")

            # Wait for Streamlit to process and rerun
            time.sleep(2)  # Initial wait for input processing

            # Wait for turn_count to increase (indicating page has updated)
            max_wait = 20  # Maximum seconds to wait
            waited = 0
            debug_info = get_debug_info(page)
            while debug_info.get("turn_count", 0) <= pre_turn_count and waited < max_wait:
                time.sleep(1)
                waited += 1
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except:
                    pass
                debug_info = get_debug_info(page)

            if waited >= max_wait:
                print(f"      ⚠️ Timeout waiting for turn update (pre={pre_turn_count}, post={debug_info.get('turn_count', 0)})")
            actual_stage = debug_info.get("stage", "Unknown")
            actual_score = debug_info.get("score", 0)
            actual_status = debug_info.get("status", "None")

            turn_result["actual"] = {
                "stage": actual_stage,
                "score": actual_score,
                "status": actual_status
            }

            detected = debug_info.get("detected_stage", "Unknown")
            next_stg = debug_info.get("next_stage", "Unknown")
            turn_cnt = debug_info.get("turn_count", 0)
            render_t = debug_info.get("render_time", "0")
            print(f"      Actual:   Stage={actual_stage}, Status={actual_status}, Score={actual_score}")
            print(f"      Debug:    Detected={detected}, NextStage={next_stg}, TurnCount={turn_cnt}")

            # Validate Stage
            if turn.expected_stage_keyword not in actual_stage:
                error = f"Stage mismatch: expected '{turn.expected_stage_keyword}' in '{actual_stage}'"
                print(f"      ❌ {error}")
                turn_result["errors"].append(error)
                turn_result["passed"] = False
            else:
                print(f"      ✅ Stage OK")

            # Validate Status
            if turn.expected_status not in actual_status:
                error = f"Status mismatch: expected '{turn.expected_status}' in '{actual_status}'"
                print(f"      ❌ {error}")
                turn_result["errors"].append(error)
                turn_result["passed"] = False
            else:
                print(f"      ✅ Status OK")

            # Validate Score
            if actual_score < turn.min_score:
                error = f"Score too low: {actual_score} < {turn.min_score}"
                print(f"      ❌ {error}")
                turn_result["errors"].append(error)
                turn_result["passed"] = False
            elif turn.max_score and actual_score > turn.max_score:
                error = f"Score too high for Alert: {actual_score} > {turn.max_score}"
                print(f"      ❌ {error}")
                turn_result["errors"].append(error)
                turn_result["passed"] = False
            else:
                print(f"      ✅ Score OK")

        except Exception as e:
            error = f"Exception: {str(e)}"
            print(f"      🔥 {error}")
            turn_result["errors"].append(error)
            turn_result["passed"] = False

        results["turns"].append(turn_result)
        if not turn_result["passed"]:
            results["passed"] = False
            results["errors"].extend(turn_result["errors"])

    # Summary
    if results["passed"]:
        print(f"\n   🎉 SCENARIO PASSED: {scenario.name}")
    else:
        print(f"\n   💀 SCENARIO FAILED: {scenario.name}")
        print(f"      Errors: {len(results['errors'])}")

    return results


def main():
    """Main entry point"""
    print("="*70)
    print("🏛️  Sales Dojo - Automated Scenario Validation")
    print("    Powered by Business Ecosystem Grand Architect")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print(f"\n🚀 Connecting to {TARGET_URL}...")
        page.goto(TARGET_URL, timeout=60000)
        page.wait_for_load_state("networkidle")
        print("✅ Connected")

        # Define scenarios to run
        scenarios = [
            SCENARIO_GOLDEN,
            SCENARIO_RUSHER,
            SCENARIO_PIVOT,
            SCENARIO_LOOPER
        ]

        all_results = []

        for scenario in scenarios:
            result = run_scenario(page, scenario)
            all_results.append(result)
            time.sleep(2)

        browser.close()

    # Final Report
    print("\n" + "="*70)
    print("📊 FINAL TEST REPORT")
    print("="*70)

    passed = sum(1 for r in all_results if r["passed"])
    failed = len(all_results) - passed

    print(f"\nTotal: {len(all_results)} scenarios")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    print("\n--- Results by Scenario ---")
    for result in all_results:
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"{status} : {result['name']}")
        if result["errors"]:
            for err in result["errors"][:3]:  # Show first 3 errors
                print(f"        → {err}")

    # Save detailed report
    report_path = "scenario_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n📝 Detailed report saved to: {report_path}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
