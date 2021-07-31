import asyncio
from args import Arguments

from computation.difficulty import compute_difficulties
from data import get_charts, load_charts
from models import Chart


async def main():
    args = Arguments().parse_args()

    charts: list[Chart] = await get_charts(args) if args.download_charts else load_charts()
    difficulties = compute_difficulties(charts)

if __name__ == '__main__':
    asyncio.run(main())