import asyncio
from payment_generator import stream_payment_signals

async def main():
    print("Starting Payment Signal Simulation...")
    print("-" * 50)
    
    try:
        # Stream 10 signals with a 0.5 second delay between them
        async for signal in stream_payment_signals(base_delay=0.5, count=200):
            print(f"[{signal.timestamp.strftime('%H:%M:%S')}] "
                  f"{signal.transaction_id[:8]}... | "
                  f"{signal.currency} {signal.amount:8.2f} | "
                  f"{signal.status:10} | "
                  f"{signal.payment_method} via {signal.merchant_id} | "
                  f"Lat: {signal.latency_ms}ms")
    except KeyboardInterrupt:
        print("\nStream stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    
    print("-" * 50)
    print("Simulation Complete.")

if __name__ == "__main__":
    asyncio.run(main())
