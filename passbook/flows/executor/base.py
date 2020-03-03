from typing import List, Optional

from structlog import get_logger

from passbook.core.models import Factor, User
from passbook.flows.executor.state import FlowState
from passbook.flows.models import FactorBinding, Flow

LOGGER = get_logger()


class FlowExecutor:

    _state: FlowState

    _flow: Flow
    _factor_bindings: List[FactorBinding]
    _pending_user: User

    _current_factor_binding: FactorBinding
    _current_factor: Factor

    def __init__(self):
        self._state = None
        self._flow = None
        self._factor_bindings = []
        self._pending_user = None
        self._current_factor = None
        self._current_factor_binding = None

    def state_restore(self):
        raise NotImplementedError()

    def state_persist(self):
        raise NotImplementedError()

    def state_cleanup(self):
        raise NotImplementedError()

    @property
    def flow(self) -> Flow:
        if not self._flow:
            self._flow = Flow.objects.get(pk=self._state.flow_pk)
        return self._flow

    @property
    def pending_factors(self) -> List[FactorBinding]:
        if self._factor_bindings:
            return self._factor_bindings

        factors = FactorBinding.objects.filter(flow=self.flow.pk).order_by("order")
        if self._state.factor_binding_last_order > 0:
            factors = factors.filter(order__gt=self._state.factor_binding_last_order)
        self._factor_bindings = list(factors)
        # TODO: When Factors have policies, check them here
        return self._factor_bindings

    @property
    def pending_user(self) -> User:
        if not self._pending_user:
            self._pending_user = User.objects.get(pk=self._state.pending_user_pk)
        return self._pending_user

    def _pop_next_factor(self) -> Optional[FactorBinding]:
        # If we don't have any more factors pending, return here
        if len(self.pending_factors) < 1:
            return None
        return self._factor_bindings.pop(0)

    def get_next_factor(self) -> Optional[Factor]:
        # Check if we've already got a factor loaded that needs solving
        if not self._current_factor:
            # Check if we have an existing FactorBinding, and pop the next one
            # we *dont* persist the state here, as this factor is still in progress
            if not self._current_factor_binding:
                # There might not be any more factors left, return none in that case
                popped_factor = self._pop_next_factor()
                if not popped_factor:
                    LOGGER.debug("B_EX: factors exhausted")
                    return None
                self._current_factor_binding = popped_factor
            # Make sure we have the correct subclass of the factor
            self._current_factor = Factor.objects.get_subclass(
                pk=self._current_factor_binding.factor
            )
        return self._current_factor

    def factor_passed(self):
        LOGGER.debug("B_EX: factor_passed", factor=self._current_factor_binding)
        self._state.factor_binding_last_order = self._current_factor_binding.order
        self._pop_next_factor()
        self.state_persist()

    def factor_failed(self):
        self.state_cleanup()

    def passed(self):
        LOGGER.debug("B_EX: Logged in", user=self.pending_user)
        self.state_cleanup()
