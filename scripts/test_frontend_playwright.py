"""
Frontend Integration Test using Playwright - with HTTP server
Tests the BriefForm component to verify:
1. Page loads correctly
2. word_limit field is NOT present (removed)
3. optimization_mode selector has correct options
4. Form validation works
"""

import asyncio
import http.server
import socketserver
import threading
import os
from playwright.async_api import async_playwright
import json


# Simple HTTP server to serve the dist folder
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory="/home/ubuntu/projects/OrganBriefOptimization/frontend/dist",
            **kwargs,
        )

    def log_message(self, format, *args):
        pass  # Suppress logging


def start_server(port=5180):
    """Start a simple HTTP server in a thread"""
    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        httpd.serve_forever()


async def test_frontend():
    """Test the BriefForm component"""

    results = {
        "test_name": "Frontend BriefForm Integration Test",
        "tests": [],
        "passed": 0,
        "failed": 0,
    }

    # Start HTTP server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    await asyncio.sleep(1)  # Give server time to start

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        console_messages = []
        page.on(
            "console",
            lambda msg: console_messages.append({"type": msg.type, "text": msg.text}),
        )

        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            print("Navigating to frontend...")
            await page.goto(
                "http://127.0.0.1:5180", wait_until="networkidle", timeout=30000
            )
            await asyncio.sleep(2)  # Wait for Vue to mount

            print("Page loaded")

            # Test 1: Check page title
            print("\nTest 1: Checking page title...")
            title = await page.title()
            if "Organ Brief" in title:
                results["tests"].append(
                    {"name": "Page title", "status": "PASS", "details": title}
                )
                results["passed"] += 1
                print(f"  PASS: {title}")
            else:
                results["tests"].append(
                    {"name": "Page title", "status": "FAIL", "details": f"Got: {title}"}
                )
                results["failed"] += 1

            # Test 2: Check word_limit is NOT in HTML
            print("\nTest 2: Verifying word_limit is removed...")
            html = await page.content()
            if "word_limit" not in html.lower():
                results["tests"].append(
                    {"name": "word_limit removed", "status": "PASS"}
                )
                results["passed"] += 1
                print("  PASS - word_limit not found")
            else:
                results["tests"].append(
                    {"name": "word_limit removed", "status": "FAIL"}
                )
                results["failed"] += 1
                print("  FAIL - word_limit found")

            # Test 3: Check optimization_mode exists
            print("\nTest 3: Checking optimization_mode selector...")
            optimization_mode = await page.query_selector("#optimization_mode")
            if optimization_mode:
                results["tests"].append(
                    {"name": "optimization_mode exists", "status": "PASS"}
                )
                results["passed"] += 1
                print("  PASS")
            else:
                results["tests"].append(
                    {"name": "optimization_mode exists", "status": "FAIL"}
                )
                results["failed"] += 1
                print("  FAIL")

            # Test 4: Check optimization_mode options
            print("\nTest 4: Checking optimization_mode options...")
            options = await page.query_selector_all("#optimization_mode option")
            option_values = []
            for opt in options:
                val = await opt.get_attribute("value")
                option_values.append(val)
            print(f"  Options: {option_values}")

            expected = ["STANDARD", "CONCISE", "DETAILED"]
            if all(opt in option_values for opt in expected):
                results["tests"].append(
                    {
                        "name": "optimization_mode options",
                        "status": "PASS",
                        "details": str(option_values),
                    }
                )
                results["passed"] += 1
                print("  PASS")
            else:
                results["tests"].append(
                    {
                        "name": "optimization_mode options",
                        "status": "FAIL",
                        "details": str(option_values),
                    }
                )
                results["failed"] += 1
                print("  FAIL")

            # Test 5: Check required fields
            print("\nTest 5: Checking required fields...")
            organ_no = await page.query_selector("#organNo")
            organ = await page.query_selector("#organ")
            if organ_no and organ:
                results["tests"].append(
                    {"name": "Required fields exist", "status": "PASS"}
                )
                results["passed"] += 1
                print("  PASS")
            else:
                results["tests"].append(
                    {"name": "Required fields exist", "status": "FAIL"}
                )
                results["failed"] += 1
                print("  FAIL")

            # Test 6: Check submit button
            print("\nTest 6: Checking submit button...")
            button = await page.query_selector('button[type="submit"]')
            if button:
                text = await button.text_content()
                results["tests"].append(
                    {
                        "name": "Submit button exists",
                        "status": "PASS",
                        "details": text.strip(),
                    }
                )
                results["passed"] += 1
                print(f"  PASS: {text.strip()}")
            else:
                results["tests"].append(
                    {"name": "Submit button exists", "status": "FAIL"}
                )
                results["failed"] += 1
                print("  FAIL")

            # Test 7: Test form validation
            print("\nTest 7: Testing form validation...")
            await page.click('button[type="submit"]')
            await asyncio.sleep(0.5)

            # Check for error messages
            errors = await page.query_selector_all(".text-red-700")
            if len(errors) > 0:
                results["tests"].append(
                    {
                        "name": "Form validation",
                        "status": "PASS",
                        "details": f"Found {len(errors)} error(s)",
                    }
                )
                results["passed"] += 1
                print(f"  PASS - Found {len(errors)} error message(s)")
            else:
                results["tests"].append({"name": "Form validation", "status": "FAIL"})
                results["failed"] += 1
                print("  FAIL")

            # Test 8: Fill form and verify
            print("\nTest 8: Testing form fill...")
            await page.fill("#organNo", "12345678")
            await page.fill("#organ", "測試公司")
            await asyncio.sleep(0.3)

            organ_no_val = await page.eval_on_selector("#organNo", "el => el.value")
            organ_val = await page.eval_on_selector("#organ", "el => el.value")

            if organ_no_val == "12345678" and organ_val == "測試公司":
                results["tests"].append({"name": "Form fill works", "status": "PASS"})
                results["passed"] += 1
                print("  PASS")
            else:
                results["tests"].append(
                    {
                        "name": "Form fill works",
                        "status": "FAIL",
                        "details": f"Got {organ_no_val}, {organ_val}",
                    }
                )
                results["failed"] += 1
                print(f"  FAIL")

            # Test 9: Test optimization_mode selection
            print("\nTest 9: Testing optimization_mode selection...")
            await page.select_option("#optimization_mode", "CONCISE")
            await asyncio.sleep(0.3)

            selected = await page.eval_on_selector(
                "#optimization_mode", "el => el.value"
            )
            if selected == "CONCISE":
                results["tests"].append(
                    {"name": "optimization_mode selection", "status": "PASS"}
                )
                results["passed"] += 1
                print("  PASS - CONCISE selected")
            else:
                results["tests"].append(
                    {
                        "name": "optimization_mode selection",
                        "status": "FAIL",
                        "details": f"Got {selected}",
                    }
                )
                results["failed"] += 1
                print(f"  FAIL - got {selected}")

            # Test 10: Check for console errors
            print("\nTest 10: Checking console errors...")
            errors = [m for m in console_messages if m["type"] == "error"]
            critical_errors = [e for e in errors if "warning" not in e["text"].lower()]
            if len(critical_errors) == 0:
                results["tests"].append({"name": "No console errors", "status": "PASS"})
                results["passed"] += 1
                print("  PASS")
            else:
                results["tests"].append(
                    {
                        "name": "No console errors",
                        "status": "FAIL",
                        "details": f"{len(critical_errors)} error(s)",
                    }
                )
                results["failed"] += 1
                for err in critical_errors[:2]:
                    print(f"  Error: {err['text'][:80]}")

            # Take screenshot
            print("\nTaking screenshot...")
            screenshot_path = "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/stage3/artifacts/frontend_form_screenshot.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved")

        except Exception as e:
            results["tests"].append(
                {"name": "Exception", "status": "FAIL", "details": str(e)}
            )
            results["failed"] += 1
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await browser.close()

    return results


async def main():
    print("=" * 60)
    print("Frontend Integration Test with Playwright")
    print("=" * 60)

    results = await test_frontend()

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"Passed: {results['passed']}/{total}")
    print(f"Failed: {results['failed']}/{total}")
    print()

    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASS" else "❌"
        print(f"{status_icon} {test['name']}: {test['status']}")
        if "details" in test:
            print(f"   {test['details']}")

    print("=" * 60)

    # Save results
    output_file = "/home/ubuntu/projects/OrganBriefOptimization/docs/test_report/v0.0.1/phase14/stage3/artifacts/frontend_playwright_test_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
