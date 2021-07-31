import asyncio

from computation.difficulty import compute_difficulties
from data import get_charts, load_charts


async def main():
    charts = load_charts()
    difficulties = compute_difficulties(charts)

if __name__ == '__main__':
    asyncio.run(main())