"""Quick test of tessellation service"""
import asyncio
import sys
sys.path.insert(0, '.')

from services.real_data_tessellation import EchteDatenTessellation

async def test():
    try:
        t = EchteDatenTessellation()
        print("Testing tessellation for Miami...")
        features = await t.generiere_risikokarte(25.77, -80.19, 'coastal', 8, 15.0)
        print(f"SUCCESS: Generated {len(features)} features")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
