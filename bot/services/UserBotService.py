from sqlalchemy.ext.asyncio import AsyncSession
from src.db.repositories import UserRepositories as UserRepo
from src.db.repositories import UserFavoriteRepositories as FavRepo

async def get_user_profile(tg_id: int, session: AsyncSession):
    return await UserRepo.read_user_by_id(tg_id, session)

async def get_user_favorites(tg_id: int, session: AsyncSession):
    return await FavRepo.read_user_favorites(user_id=tg_id, session=session)