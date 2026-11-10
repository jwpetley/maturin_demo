from dataclasses import dataclass

from . import _native


@dataclass(slots=True)
class Position:
    symbol: str
    quantity: int
    unit_price: int
    fee_bps: int
    active: bool = True


@dataclass(slots=True)
class Portfolio:
    name: str
    positions: list[Position]

    def value_python(self) -> int:
        total = 0
        for position in self.positions:
            if position.active:
                quantity = position.quantity
                modeled_value = quantity * position.unit_price
                for _ in range(12):
                    modeled_value = (
                        modeled_value * 1_000_003 + quantity
                    ) % 1_000_000_007
                fee = modeled_value * position.fee_bps // 10_000
                total += modeled_value - fee
        return total

    def value_rust(self) -> int:
        return _native.portfolio_value(self)


def make_portfolio(count: int) -> Portfolio:
    positions = [
        Position(
            symbol=f"SYM{index % 100:03}",
            quantity=1 + (index * 31) % 50,
            unit_price=100 + (index * 97) % 10_000,
            fee_bps=(index * 7) % 26,
            active=index % 8 != 0,
        )
        for index in range(count)
    ]
    return Portfolio(name="Demo portfolio", positions=positions)
