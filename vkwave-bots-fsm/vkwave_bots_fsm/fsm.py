from enum import Enum, auto

from vkwave_bots.dispatching.events.base import BaseEvent
from vkwave_bots_storage.base import AbstractStorage
from vkwave_bots_storage.storages import Storage
from vkwave_bots_storage.types import Key
from vkwave_bots_fsm.types import StateId
import typing


class ForWhat(Enum):
    FOR_CHAT = auto()
    FOR_USER = auto()
    FOR_USER_IN_CHAT = auto()  # default


def create_state_id(event: BaseEvent, for_what: ForWhat) -> StateId:
    res: str

    template = "__vkwave_{for_what}_{peer_id}_{from_id}__"
    from_id = event.object.object.message.from_id
    peer_id = event.object.object.message.peer_id

    is_pm = from_id == peer_id
    is_chat = not is_pm
    if for_what is ForWhat.FOR_CHAT:
        if not is_chat:
            raise ValueError("it's not a chat")
        res = template.format(for_what="chat", peer_id=peer_id, from_id=peer_id)
    elif for_what is ForWhat.FOR_USER:
        if not is_pm:
            raise ValueError("it's not a pm")
        res = template.format(for_what="user", peer_id=from_id, from_id=from_id)
    else:
        if not is_chat:
            raise ValueError("it's not a chat")
        res = template.format(for_what="userInChat", peer_id=peer_id, from_id=from_id)

    return StateId(res)


class State:
    def __init__(self, title: str):
        self.title = title


class FiniteStateMachine:
    def __init__(self, storage: typing.Optional[AbstractStorage] = None):
        self.storage = storage or Storage()

    async def set_state(
        self, state: State, event: BaseEvent, for_what: ForWhat, extra_state_data=None,
    ) -> None:
        sid = Key(create_state_id(event, for_what))
        if extra_state_data is None:
            extra_state_data = {}

        if await self.storage.contains(sid):
            current_data = await self.storage.get(sid)
            current_data["__vkwave_fsm_state__"] = state.title
            current_data.update(extra_state_data)
            return await self.storage.put(sid, current_data)

        storage_data = {"__vkwave_fsm_state__": state.title}
        storage_data.update(extra_state_data)
        return await self.storage.put(sid, storage_data)

    async def add_data(
        self, event: BaseEvent, for_what: ForWhat, state_data: dict
    ) -> None:
        sid = Key(create_state_id(event, for_what))

        data = await self.storage.get(sid)
        data.update(state_data)
        return await self.storage.put(sid, data)

    async def get_data(self, event: BaseEvent, for_what: ForWhat) -> None:
        sid = Key(create_state_id(event, for_what))
        return await self.storage.get(sid)

    async def finish(self, event: BaseEvent, for_what: ForWhat) -> None:
        sid = Key(create_state_id(event, for_what))
        return await self.storage.delete(sid)
