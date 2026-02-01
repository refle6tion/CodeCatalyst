import asyncio
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

@dataclass
class PaymentSignal:
    transaction_id: str
    timestamp: datetime
    amount: float
    currency: str
    status: str
    merchant_id: str
    payment_method: str
    latency_ms: int

async def stream_payment_signals(
    base_delay: float = 1.0, 
    count: Optional[int] = None
) -> AsyncGenerator[PaymentSignal, None]:
    """
    Simulates a live stream of payment signals with temporal correlation and outages.

    Args:
        base_delay: Base time to wait between yielding signals.
        count: Number of signals to yield. If None, yields indefinitely.
    """
    generated_count = 0
    
    # State for temporal correlation
    current_amount = 100.0
    is_burst_mode = False
    burst_probability = 0.3
    
    # State for Outage Simulation
    outage_target = None # Can be a merchant_id or currency code
    outage_type = None   # "MERCHANT" or "CURRENCY"
    outage_remaining_signals = 0
    
    currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "INR"]
    # Fixed merchants for better analysis
    merchants = [
        "merch_amazon", "merch_uber", "merch_netflix", "merch_spotify",
        "merch_target", "merch_walmart", "merch_starbucks", "merch_apple",
        "merch_steam", "merch_airbnb"
    ]
    statuses = ["SUCCESS", "PENDING", "FAILED", "DECLINED"]
    payment_methods = ["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "APPLE_PAY", "GOOGLE_PAY"]
    
    while count is None or generated_count < count:
        # --- 1. Outage Management ---
        # If no active outage, small chance to start one
        if outage_remaining_signals <= 0:
            outage_target = None
            outage_type = None
            
            if random.random() < 0.1: # 10% chance per signal to start an outage
                outage_remaining_signals = random.randint(20, 50)
                if random.random() < 0.5:
                    outage_type = "MERCHANT"
                    outage_target = random.choice(merchants)
                else:
                    outage_type = "CURRENCY"
                    outage_target = random.choice(currencies)
                # print(f"DEBUG: Starting outage for {outage_target} ({outage_type})") 
        else:
            outage_remaining_signals -= 1

        # --- 2. Traffic Bursts ---
        if random.random() < burst_probability:
            is_burst_mode = not is_burst_mode
            
        if is_burst_mode:
            current_delay = random.uniform(0.05, 0.2) * base_delay
        else:
            current_delay = random.uniform(0.8, 1.5) * base_delay

        await asyncio.sleep(current_delay)
        
        # --- 3. Generate Signal Data ---
        # Random Walk for Amount
        change_factor = random.uniform(0.9, 1.1)
        current_amount *= change_factor
        current_amount = max(1.0, min(current_amount, 5000.0))
        
        # Latency
        latency_ms = int(random.lognormvariate(2, 0.5) * 10)
        
        # Selection
        currency = random.choice(currencies)
        merchant = random.choice(merchants)
        status_weights = [0.8, 0.1, 0.05, 0.05] # Default weights
        
        # --- 4. Apply Outage Effects ---
        if outage_target:
            if (outage_type == "MERCHANT" and merchant == outage_target) or \
               (outage_type == "CURRENCY" and currency == outage_target):
                # 90% failure rate for the target
                status_weights = [0.1, 0.0, 0.8, 0.1] 
                
        status = random.choices(statuses, weights=status_weights)[0]
        
        signal = PaymentSignal(
            transaction_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            amount=round(current_amount, 2),
            currency=currency,
            status=status,
            merchant_id=merchant,
            payment_method=random.choice(payment_methods),
            latency_ms=latency_ms
        )
        
        yield signal
        generated_count += 1
