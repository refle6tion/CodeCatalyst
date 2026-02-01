import asyncio
import requests
import json
import dataclasses
from datetime import datetime
from payment_generator import stream_payment_signals
from payment_analyzer import PaymentAnalyzer

WEBHOOK_URL = "http://localhost:5678/webhook/db3aa95e-6cb0-4108-8907-50f1860d9c28"

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

async def main():
    analyzer = PaymentAnalyzer(window_size=30)
    print("Starting Live Payment Analysis...")
    print("Collecting data for LLM Prompt Generation...")
    print("-" * 60)
    
    all_signals = []

    try:
        # Stream 200 signals
        async for signal in stream_payment_signals(base_delay=0.1, count=200):
            # 1. Print simple log
            status_icon = "[OK]" if signal.status == "SUCCESS" else "[X] "
            print(f"{status_icon} {signal.currency} {signal.amount:6.2f} | {signal.latency_ms}ms")
            
            # 2. Collect for batch analysis
            all_signals.append(dataclasses.asdict(signal))
                
    except KeyboardInterrupt:
        print("\nAnalysis stopped.")
    finally:
        if all_signals:
            print(f"\nAnalyzing {len(all_signals)} signals...")
            
            # Generate Prompt
            prompt = analyzer.generate_analysis_prompt(all_signals)
            
            print("-" * 40)
            print("GENERATED PROMPT:")
            print(prompt)
            print("-" * 40)
            
            print("Sending prompt to webhook...")
            try:
                # Send the prompt wrapped in a JSON object
                payload = {"prompt": prompt}
                
                response = requests.post(
                    WEBHOOK_URL, 
                    json=payload
                )
                print(f"Prompt sent! Status Code: {response.status_code}")
                
                print("-" * 40)
                print("LLM ANALYSIS RESPONSE:")
                try:
                    # Try to parse as JSON first (n8n might return JSON)
                    resp_json = response.json()
                    # Check for common text fields
                    if isinstance(resp_json, dict) and 'text' in resp_json:
                        print(resp_json['text'])
                    elif isinstance(resp_json, dict) and 'output' in resp_json:
                        print(resp_json['output'])
                    elif isinstance(resp_json, dict) and 'message' in resp_json:
                        print(resp_json['message'])
                    else:
                        # Fallback to pretty-printed JSON
                        print(json.dumps(resp_json, indent=2))
                except ValueError:
                    # Not JSON, print raw text
                    if not response.text.strip():
                        print("(No response body returned from webhook)")
                    else:
                        print(response.text)
                print("-" * 40)
                    
            except Exception as e:
                print(f"Failed to send prompt: {e}")

if __name__ == "__main__":
    asyncio.run(main())
