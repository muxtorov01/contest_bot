"""Konkurs yaratish/tahrirlash uchun FSM holatlari."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CreateContestStates(StatesGroup):
    title = State()
    description = State()
    start_at = State()
    end_at = State()
    confirm = State()


class RescheduleContestStates(StatesGroup):
    choose_field = State()
    new_value = State()


class AddChannelStates(StatesGroup):
    waiting_channel = State()


class AddAdminStates(StatesGroup):
    waiting_user_id = State()
    waiting_role = State()


class RemoveAdminStates(StatesGroup):
    waiting_user_id = State()


class BroadcastStates(StatesGroup):
    waiting_text = State()
    confirm = State()


class SearchUserStates(StatesGroup):
    waiting_query = State()
