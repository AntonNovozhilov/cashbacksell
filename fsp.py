from aiogram.fsm.state import State, StatesGroup

class PostForm(StatesGroup):
    """Состояния при формировании поста."""
    
    title = State()
    price = State()
    cashback = State()
    photo = State()