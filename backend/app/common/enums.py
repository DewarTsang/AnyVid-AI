from enum import StrEnum, unique


@unique
class EnvironmentEnum(StrEnum):
    """应用运行环境（开发 / 生产）。"""

    DEV = "dev"
    PROD = "prod"


PLANS = {
    "monthly": {
        "name": "AnyVid AI VIP 月度会员",
        "amount": 990,
        "currency": "cny",
    },
}
