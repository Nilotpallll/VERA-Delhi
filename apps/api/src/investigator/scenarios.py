"""End-to-end evaluation scenarios for VERA Investigator.

Scenarios test full lifecycle from multimodal input to report generation.
"""

from typing import Any

EVALUATION_SCENARIOS: dict[str, dict[str, Any]] = {
    # 1. Benign Investment Message
    "benign_investment_message": {
        "description": "Legitimate investment advisory from verified broker Zerodha with standard statutory disclaimers.",
        "inputs": [
            {
                "id": "inp_sc1",
                "type": "TEXT",
                "value": "Market update from Zerodha Broking Limited (SEBI Reg: INZ000031633). Investments are subject to market risks. Read all scheme related documents carefully before investing.",
            }
        ],
        "expected": {
            "risk_level": "LOW",
            "max_score": 24.0,
            "status": "COMPLETED",
            "signals_should_not_include": ["guaranteed_return", "unverified_entity", "payment_mismatch"],
        },
    },

    # 2. Guaranteed-Return Scam
    "guaranteed_return_scam": {
        "description": "Classic WhatsApp high-yield investment scam promising guaranteed 3X return with UPI deposit.",
        "inputs": [
            {
                "id": "inp_sc2",
                "type": "TEXT",
                "value": "🚨 EXCLUSIVE OPPORTUNITY 🚨 Invest ₹10,000 and get 100% guaranteed 3X return in 7 days! Zero risk assured profit. Pay via UPI: quick.returns@paytm immediately. Limited slots!",
            }
        ],
        "expected": {
            "min_score": 35.0,
            "status": "COMPLETED",
            "signals_must_include": ["guaranteed_return", "payment_mismatch"],
        },
    },

    # 3. Fake SEBI Representative
    "fake_sebi_representative": {
        "description": "Scammer impersonating authorized SEBI Research Analyst with fabricated registration number.",
        "inputs": [
            {
                "id": "inp_sc3",
                "type": "TEXT",
                "value": "I am Dr. Sharma, Senior SEBI Certified Research Analyst (Registration No: INA999999999). Join my VIP channel for daily insider equity tips.",
            }
        ],
        "expected": {
            "min_score": 25.0,
            "status": "COMPLETED",
            "signals_must_include": ["unverified_entity"],
        },
    },

    # 4. Fake Trading Website
    "fake_trading_website": {
        "description": "Phishing portal masquerading as Zerodha on a suspicious .xyz top-level domain.",
        "inputs": [
            {
                "id": "inp_sc4",
                "type": "TEXT",
                "value": "Official Zerodha Trade Terminal update! Log in to secure your portfolio at https://zerodha-trade-vip.xyz/login",
            }
        ],
        "expected": {
            "min_score": 20.0,
            "status": "COMPLETED",
            "signals_must_include": ["domain_mismatch"],
        },
    },

    # 5. Suspicious APK
    "suspicious_apk": {
        "description": "Rogue Android binary purporting to be a high-yield algorithmic trading platform.",
        "inputs": [
            {
                "id": "inp_sc5",
                "type": "APK",
                "value": "fake_pro_trader_v2.apk",
            }
        ],
        "mock_evidence": [
            {
                "id": "ev_mock_apk",
                "type": "suspicious_apk",
                "source_reference": "fake_pro_trader_v2.apk",
                "metadata": {"dangerous_permissions": ["RECEIVE_SMS", "SYSTEM_ALERT_WINDOW"]},
            }
        ],
        "expected": {
            "min_score": 25.0,
            "status": "COMPLETED",
            "signals_must_include": ["suspicious_apk"],
        },
    },

    # 6. Manipulated Investment Video
    "manipulated_investment_video": {
        "description": "Deepfake video of prominent business figure promoting fraudulent crypto-trading scheme.",
        "inputs": [
            {
                "id": "inp_sc6",
                "type": "VIDEO",
                "value": "deepfake_endorsement.mp4",
            }
        ],
        "mock_evidence": [
            {
                "id": "ev_mock_vid",
                "type": "deepfake_signal",
                "source_reference": "deepfake_endorsement.mp4",
                "metadata": {"mesonet_score": 0.94},
            }
        ],
        "expected": {
            "min_score": 25.0,
            "status": "COMPLETED",
            "signals_must_include": ["deepfake_signal"],
        },
    },

    # 7. Mixed-Evidence Case
    "mixed_evidence_case": {
        "description": "Sophisticated multi-modal scam combining guaranteed return, unverified SEBI claim, fake website, and withdrawal fee.",
        "inputs": [
            {
                "id": "inp_sc7_1",
                "type": "TEXT",
                "value": "Guaranteed 100% profit in 15 days by SEBI Analyst (Reg: INA888888888). Visit https://zerodha-trade-vip.xyz and deposit to scam.invest@upi. Note: 10% withdrawal fee applies.",
            }
        ],
        "expected": {
            "risk_level": "CRITICAL",
            "min_score": 75.0,
            "score_cap": 100.0,
            "status": "COMPLETED",
            "signals_must_include": ["guaranteed_return", "unverified_entity", "domain_mismatch", "payment_mismatch", "withdrawal_fee"],
        },
    },

    # 8. Insufficient-Evidence Case
    "insufficient_evidence_case": {
        "description": "Vague, uninformative single message without claims, financial calls, or technical artifacts.",
        "inputs": [
            {
                "id": "inp_sc8",
                "type": "TEXT",
                "value": "   ",
            }
        ],
        "expected": {
            "status": "INSUFFICIENT_EVIDENCE",
            "risk_score": 0.0,
            "risk_level": "INCONCLUSIVE",
        },
    },
}
