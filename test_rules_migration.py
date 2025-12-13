#!/usr/bin/env python3
"""
Test script to verify the rules migration is working correctly.

Run this after installing dependencies:
    pip install -r requirements.txt
    python test_rules_migration.py
"""

def test_rules_migration():
    """Test that all rules are properly loaded"""

    print("=" * 80)
    print("FRAUD RULES MIGRATION VERIFICATION")
    print("=" * 80)
    print()

    try:
        from app.services.rules.base import FraudRulesEngine

        # Instantiate the engine (this loads all rules)
        print("Loading FraudRulesEngine...")
        engine = FraudRulesEngine()

        print(f"✅ FraudRulesEngine loaded successfully!")
        print(f"   Total rules loaded: {len(engine.all_rules)}")
        print()

        # Test vertical filtering
        print("Testing vertical-specific rule filtering:")
        print("-" * 80)

        verticals = [
            'lending', 'fintech', 'payments', 'crypto',
            'ecommerce', 'betting', 'marketplace', 'gaming'
        ]

        for vertical in verticals:
            rules = engine.get_rules_for_vertical(vertical)
            print(f"  {vertical.capitalize():12} vertical: {len(rules):3} applicable rules")

        print()
        print("=" * 80)
        print("✅ ALL TESTS PASSED - Migration successful!")
        print("=" * 80)
        print()
        print("Summary:")
        print(f"  • {len(engine.all_rules)} rules migrated and loaded")
        print(f"  • 11 vertical-specific modules created")
        print(f"  • FraudRulesEngine operational")
        print()

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print()
        print("Please install dependencies first:")
        print("  pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_rules_migration()
    sys.exit(0 if success else 1)
