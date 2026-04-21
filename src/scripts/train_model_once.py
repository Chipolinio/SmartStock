import asyncio

from src.db.database import AsyncSessionLocal
from src.services.MLService import run_model_training


async def main() -> None:
    async with AsyncSessionLocal() as session:
        try:
            trained = await run_model_training(session)
            if trained:
                await session.commit()
                print("Model training on deploy completed successfully")
            else:
                print("Model training skipped: not enough data")
        except Exception as exc:
            await session.rollback()
            # Do not break deployment if training fails.
            print(f"Model training failed during deploy: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
