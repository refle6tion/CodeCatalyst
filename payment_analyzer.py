import textwrap
from collections import Counter
from typing import List
from payment_generator import PaymentSignal

class PaymentAnalyzer:
    def __init__(self, window_size: int = 20):
        # Window size kept for compatibility
        pass
        
    def generate_analysis_prompt(self, signals: List[dict]) -> str:
        """
        Generates a summary prompt for an LLM based on a list of payment signal dictionaries.
        """
        if not signals:
            return "No payment signals to analyze."

        total_signals = len(signals)
        
        # Calculate aggregate metrics
        failed_signals = [s for s in signals if s['status'] in ("FAILED", "DECLINED")]
        failure_count = len(failed_signals)
        failure_rate = failure_count / total_signals if total_signals > 0 else 0
        
        latencies = [s['latency_ms'] for s in signals]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        # Analyze failures by Merchant and Currency
        failed_merchants = [s['merchant_id'] for s in failed_signals]
        failed_currencies = [s['currency'] for s in failed_signals]
        
        merchant_counts = Counter(failed_merchants).most_common(3)
        currency_counts = Counter(failed_currencies).most_common(3)
        
        # Representative samples
        problematic_samples = [
            s for s in signals 
            if s['status'] in ("FAILED", "DECLINED") or s['latency_ms'] > 200
        ]
        
        sample_lines = ""
        for s in problematic_samples[:10]:
            sample_lines += (
                f"- [{s['timestamp']}] "
                f"merchant={s['merchant_id']} "
                f"currency={s['currency']} "
                f"amount={s['amount']} "
                f"status={s['status']} "
                f"latency={s['latency_ms']}ms\n"
            )

        # Construct the prompt using textwrap.dedent for clean formatting
        prompt = textwrap.dedent(f"""
            - Total Transactions: {total_signals}
            - Failure Rate: {failure_rate:.1%} ({failure_count} failures)
            - Average Latency: {avg_latency:.0f}ms
            - Max Latency: {max_latency}ms

            FAILURE CONCENTRATION:
            - Failed Merchants (count): {', '.join([f'{m}: {c}' for m, c in merchant_counts])}
            - Failed Currencies (count): {', '.join([f'{c}: {cnt}' for c, cnt in currency_counts])}

            SAMPLE ANOMALOUS TRANSACTIONS (failures or latency > 200ms):
            {sample_lines}
        """).strip()
        
        return prompt
