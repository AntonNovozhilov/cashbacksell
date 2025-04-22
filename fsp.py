from aiogram.fsm.state import State, StatesGroup

class PostForm(StatesGroup):
    """Состояния при формировании поста."""
    
    name = State()
    description = State()
    price = State()
    cashback = State()
    photo = State()