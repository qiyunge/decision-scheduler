from __future__ import annotations
from typing import Any, Callable, ClassVar, TypeAlias
from ...support.events import DomainEvent, DomainInitiatedEvent,NaturalProcessInitiatedEvent
from ..actions import Action
from ...support.exceptions import (
    TransitionFrozenError,
    TransitionRegistrationError,
    UnknownActionHandlerError,
)
from ...models.state import SchedulingState

class Transition:
    """
    Base class for transitions.
    """
    pass


# instance-level runtime handler:
# (state, action) -> tuple[DomainEvent, ...]
RuntimeHandler: TypeAlias = Callable[[Any, Action], tuple[DomainEvent, ...]]

# class-level static handler:
# (self, state, action) -> tuple[DomainEvent, ...]
StaticHandler: TypeAlias = Callable[[Transition, SchedulingState, Action], tuple[DomainEvent, ...]]


# =========================
# Decorator for static registration
# =========================

def action_handler(action_type: type[Action]) -> Callable[[StaticHandler], StaticHandler]:
    """
    Mark a method as the static handler for an exact action type.
    """
    def decorator(func: StaticHandler) -> StaticHandler:
        setattr(func, "__handles_action_type__", action_type)
        return func
    return decorator


# =========================
# Transition base
# =========================

class StaticRuntimeActionTransition:
    """
    Transition with:
    1. static class-level handler registration as the main mechanism
    2. optional runtime handler registration per instance
    3. exact action type matching only (no MRO / no inheritance fallback)
    4. freeze support
    """

    _static_handlers: ClassVar[dict[type[Action], StaticHandler]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # collect inherited static handlers first
        static_handlers: dict[type[Action], StaticHandler] = {}

        for base in cls.__bases__:
            base_registry = getattr(base, "_static_handlers", None)
            if base_registry:
                static_handlers.update(base_registry)

        # collect handlers declared in current class body
        for _, value in cls.__dict__.items():
            action_type = getattr(value, "__handles_action_type__", None)
            if action_type is None:
                continue

            if action_type in static_handlers:
                raise TransitionRegistrationError(
                    f"{cls.__name__} already has a static handler for "
                    f"{action_type.__name__}."
                )

            static_handlers[action_type] = value

        cls._static_handlers = static_handlers

    def __init__(self) -> None:
        self._runtime_handlers: dict[type[Action], RuntimeHandler] = {}
        self._frozen: bool = False

    # -------------------------
    # freeze
    # -------------------------

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        self._frozen = True

    # -------------------------
    # runtime registration
    # -------------------------

    def register_runtime_handler(
        self,
        action_type: type[Action],
        handler: RuntimeHandler,
        *,
        override: bool = False,
    ) -> None:
        """
        Register a runtime handler for an exact action type.

        Rules:
        - no MRO support
        - if override=False:
            cannot replace an existing runtime handler
            cannot shadow a static handler
        - if override=True:
            may replace runtime or shadow static
        - frozen transition cannot be modified
        """
        if self._frozen:
            raise TransitionFrozenError(
                f"{self.__class__.__name__} is frozen; runtime registration is disabled."
            )

        if not override:
            if action_type in self._runtime_handlers:
                raise TransitionRegistrationError(
                    f"Runtime handler for {action_type.__name__} already exists."
                )
            if action_type in self._static_handlers:
                raise TransitionRegistrationError(
                    f"Static handler for {action_type.__name__} already exists; "
                    f"use override=True to shadow it."
                )

        self._runtime_handlers[action_type] = handler

    def unregister_runtime_handler(self, action_type: type[Action]) -> None:
        if self._frozen:
            raise TransitionFrozenError(
                f"{self.__class__.__name__} is frozen; runtime unregistration is disabled."
            )

        self._runtime_handlers.pop(action_type, None)

    # -------------------------
    # resolve
    # -------------------------

    def resolve_action(self, state: SchedulingState, action: Action) -> tuple[DomainInitiatedEvent, ...]:
        action_type = type(action)
        print(f"Resolving action of type {action_type.__name__} in transition {self.__class__.__name__}...")

        # 1. runtime handlers first
        runtime_handler = self._runtime_handlers.get(action_type)
        if runtime_handler is not None:
            return runtime_handler(state, action)

        # 2. static handlers second
        static_handler = self._static_handlers.get(action_type)
        if static_handler is not None:
            return static_handler(self, state, action)

        raise UnknownActionHandlerError(
            f"No handler registered for exact action type: {action_type.__name__}"
        )
    
    def resolve_natural_process(self, state: SchedulingState) -> tuple[DomainInitiatedEvent, ...]:
        """
        Resolve any natural process that should occur in the current state
        without an external action. This can be used to advance time or trigger
        automatic events.
        """
        # By default, do nothing. Subclasses can override this method.
        next_completion = state.next_completion_time
        next_release = state.next_release_time

        next_time = min(next_completion, next_release) if next_completion is not None and next_release is not None else next_completion or next_release

        if next_time is not None and next_time > state.current_time:
            natural_effects = state.natural_effects_at(next_time)
            
            return (
                NaturalProcessInitiatedEvent(time = state.current_time, new_time = next_time, scheduled_effects=natural_effects),
            )
        
        return ()