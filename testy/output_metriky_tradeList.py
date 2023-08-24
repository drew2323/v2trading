import pandas as pd
from v2realbot.utils.utils import AttributeDict

from v2realbot.common.model import TradeEvent, TradeUpdate, Order
from v2realbot.enums.enums import OrderSide, OrderStatus, OrderType
import datetime
from uuid import UUID

#testing tradelist
tradeList = [
        TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('67affc55-fa98-446f-8ac0-eb0bb494f450'),
        order=Order(
            id=UUID('ae8b1fff-8a87-4ec2-af7d-48765c62afc5'),
            submitted_at=datetime.datetime(2023, 3, 24, 17, 58, 1, 538364),
            filled_at=datetime.datetime(2023, 3, 24, 17, 58, 30, 735317),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.56,
            side=OrderSide.BUY,
            limit_price=42.56
        ),
        timestamp=datetime.datetime(2023, 3, 24, 17, 58, 30, 735317),
        position_qty=10.0,
        price=42.56,
        qty=10.0,
        value=425.6,
        cash=99574.4,
        pos_avg_price=42.56
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('51b872ed-98f1-4540-af13-6d8beb6ab660'),
        order=Order(
            id=UUID('5cae451b-6c46-47d5-8a43-023569eebcac'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 0, 43, 790484),
            filled_at=datetime.datetime(2023, 3, 24, 18, 0, 46, 336552),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.51,
            side=OrderSide.BUY,
            limit_price=42.51
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 0, 46, 336552),
        position_qty=20.0,
        price=42.51,
        qty=10.0,
        value=425.09999999999997,
        cash=99149.29999999999,
        pos_avg_price=42.535000000000004
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('86e67324-8b74-4f67-bac7-16f2564f117d'),
        order=Order(
            id=UUID('f04a52b4-74e0-4de8-9ec3-a89d608e2c8d'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 3, 20, 914489),
            filled_at=datetime.datetime(2023, 3, 24, 18, 3, 22, 529390),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.44,
            side=OrderSide.BUY,
            limit_price=42.44
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 3, 22, 529390),
        position_qty=30.0,
        price=42.44,
        qty=10.0,
        value=424.4,
        cash=98724.9,
        pos_avg_price=42.50333333333333
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('8ef5eb96-9dfa-486b-b52b-bd1cc10ab75d'),
        order=Order(
            id=UUID('fae4fd0d-d1e4-46e2-85e5-f32708780e77'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 3, 22, 575390),
            filled_at=datetime.datetime(2023, 3, 24, 18, 5, 37, 585264),
            canceled_at=None,
            symbol='C',
            qty=30,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=30,
            filled_avg_price=42.52,
            side=OrderSide.SELL,
            limit_price=42.52
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 5, 37, 585264),
        position_qty=0.0,
        price=42.52,
        qty=30.0,
        value=1275.6000000000001,
        cash=100000.5,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('1b3ea95a-b51c-4894-83e1-82364695047a'),
        order=Order(
            id=UUID('40aef04b-677f-4429-9a6f-05de170df1ae'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 10, 45, 566915),
            filled_at=datetime.datetime(2023, 3, 24, 18, 11, 6, 387022),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.42,
            side=OrderSide.BUY,
            limit_price=42.42
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 11, 6, 387022),
        position_qty=10.0,
        price=42.42,
        qty=10.0,
        value=424.20000000000005,
        cash=99576.3,
        pos_avg_price=42.42
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('44baaa7c-4ff6-4e16-ac4a-0ae45a050c03'),
        order=Order(
            id=UUID('21b961ac-8129-4800-babd-81bb87eccfda'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 13, 20, 777011),
            filled_at=datetime.datetime(2023, 3, 24, 18, 14, 38, 586145),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.38,
            side=OrderSide.BUY,
            limit_price=42.38
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 14, 38, 586145),
        position_qty=20.0,
        price=42.38,
        qty=10.0,
        value=423.8,
        cash=99152.5,
        pos_avg_price=42.4
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('28c9f825-4300-46ce-b73e-3af795a836a9'),
        order=Order(
            id=UUID('28c897f5-cb12-4b2c-9b20-abde056e1b12'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 14, 38, 632145),
            filled_at=datetime.datetime(2023, 3, 24, 18, 15, 13, 203500),
            canceled_at=None,
            symbol='C',
            qty=20,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=20,
            filled_avg_price=42.42,
            side=OrderSide.SELL,
            limit_price=42.42
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 15, 13, 203500),
        position_qty=0.0,
        price=42.42,
        qty=20.0,
        value=848.4000000000001,
        cash=100000.9,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('445a98ae-6fbe-415d-88e8-f98f5c6fb411'),
        order=Order(
            id=UUID('f1e8412c-7e36-4d0c-97a7-88e5dbab9b25'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 20, 0, 372031),
            filled_at=datetime.datetime(2023, 3, 24, 18, 20, 10, 239271),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.39,
            side=OrderSide.BUY,
            limit_price=42.39
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 20, 10, 239271),
        position_qty=10.0,
        price=42.39,
        qty=10.0,
        value=423.9,
        cash=99577.0,
        pos_avg_price=42.39
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('e2e5cf75-6517-459b-89f8-f967a3442737'),
        order=Order(
            id=UUID('cf1cab4c-9e39-46a9-a804-d2e2337340bf'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 20, 10, 285271),
            filled_at=datetime.datetime(2023, 3, 24, 18, 20, 31, 861599),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.41,
            side=OrderSide.SELL,
            limit_price=42.41
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 20, 31, 861599),
        position_qty=0.0,
        price=42.41,
        qty=10.0,
        value=424.09999999999997,
        cash=100001.1,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('0f5308ae-bea1-4412-8922-344f6dac10ef'),
        order=Order(
            id=UUID('6f16c0c0-a86e-4e6f-b07e-7eb76347b223'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 43, 20, 376929),
            filled_at=datetime.datetime(2023, 3, 24, 18, 45, 52, 906738),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.99,
            side=OrderSide.BUY,
            limit_price=42.99
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 45, 52, 906738),
        position_qty=10.0,
        price=42.99,
        qty=10.0,
        value=429.90000000000003,
        cash=99571.20000000001,
        pos_avg_price=42.99
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('98f17b2e-4392-47e5-8697-c23878e1c71a'),
        order=Order(
            id=UUID('afc5a626-c3cb-4cf9-b887-7571dded2f6c'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 45, 52, 952738),
            filled_at=datetime.datetime(2023, 3, 24, 18, 46, 0, 627175),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=43.01,
            side=OrderSide.SELL,
            limit_price=43.01
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 46, 0, 627175),
        position_qty=0.0,
        price=43.01,
        qty=10.0,
        value=430.09999999999997,
        cash=100001.30000000002,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('5431e393-291c-4828-be51-706acc39deda'),
        order=Order(
            id=UUID('a3a6a1d1-8bf8-4fc6-995d-0d0766443c55'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 49, 41, 540044),
            filled_at=datetime.datetime(2023, 3, 24, 18, 50, 47, 441926),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.93,
            side=OrderSide.BUY,
            limit_price=42.93
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 50, 47, 441926),
        position_qty=10.0,
        price=42.93,
        qty=10.0,
        value=429.3,
        cash=99572.00000000001,
        pos_avg_price=42.93
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('f10ca407-0604-4e2e-b0cf-4e4243e57947'),
        order=Order(
            id=UUID('246d819c-6e1d-4fc0-a91e-17404fcc5cea'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 50, 47, 487926),
            filled_at=datetime.datetime(2023, 3, 24, 18, 54, 23, 727098),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.95,
            side=OrderSide.SELL,
            limit_price=42.95
        ),
        timestamp=datetime.datetime(2023, 3, 24, 18, 54, 23, 727098),
        position_qty=0.0,
        price=42.95,
        qty=10.0,
        value=429.5,
        cash=100001.50000000001,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('9fcef2d1-2b55-4a74-9927-8463a74e75e2'),
        order=Order(
            id=UUID('f250e354-2291-499f-b1f0-d56788211959'),
            submitted_at=datetime.datetime(2023, 3, 24, 18, 52, 20, 117195),
            filled_at=datetime.datetime(2023, 3, 24, 19, 5, 39, 193071),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.86,
            side=OrderSide.BUY,
            limit_price=42.86
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 5, 39, 193071),
        position_qty=10.0,
        price=42.86,
        qty=10.0,
        value=428.6,
        cash=99572.90000000001,
        pos_avg_price=42.86
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('ea4b0db4-998e-4e2a-b614-98b157106164'),
        order=Order(
            id=UUID('570e9c37-5c4e-4437-9dd4-a642029ca6a7'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 5, 39, 239071),
            filled_at=datetime.datetime(2023, 3, 24, 19, 5, 46, 747462),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.88,
            side=OrderSide.SELL,
            limit_price=42.88
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 5, 46, 747462),
        position_qty=0.0,
        price=42.88,
        qty=10.0,
        value=428.8,
        cash=100001.70000000001,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('abf993dc-5aee-4b89-b48c-92bbfcb4efe4'),
        order=Order(
            id=UUID('f3be9459-1c89-4594-bee0-b64ace83a12e'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 7, 22, 109412),
            filled_at=datetime.datetime(2023, 3, 24, 19, 7, 25, 509392),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.79,
            side=OrderSide.BUY,
            limit_price=42.79
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 7, 25, 509392),
        position_qty=10.0,
        price=42.79,
        qty=10.0,
        value=427.9,
        cash=99573.80000000002,
        pos_avg_price=42.79
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('b30b01cf-b0da-4166-a5ee-9e398ce0caf7'),
        order=Order(
            id=UUID('44687505-271f-423d-b5eb-4022a3b0042e'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 7, 25, 555392),
            filled_at=datetime.datetime(2023, 3, 24, 19, 7, 49, 238057),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.81,
            side=OrderSide.SELL,
            limit_price=42.81
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 7, 49, 238057),
        position_qty=0.0,
        price=42.81,
        qty=10.0,
        value=428.1,
        cash=100001.90000000002,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('3d0bde12-75e4-4589-b51d-98f351c27f51'),
        order=Order(
            id=UUID('b4d1deb5-bedb-4792-87a2-d93d7a791245'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 42, 0, 124666),
            filled_at=datetime.datetime(2023, 3, 24, 19, 42, 3, 369522),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.97,
            side=OrderSide.BUY,
            limit_price=42.97
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 42, 3, 369522),
        position_qty=10.0,
        price=42.97,
        qty=10.0,
        value=429.7,
        cash=99572.20000000003,
        pos_avg_price=42.97
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('726bc5e6-94fd-4618-bee0-91339dbfa88c'),
        order=Order(
            id=UUID('b32bb6d0-c972-45a5-b6ac-144273e956ea'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 42, 3, 415522),
            filled_at=datetime.datetime(2023, 3, 24, 19, 42, 34, 428260),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.99,
            side=OrderSide.SELL,
            limit_price=42.99
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 42, 34, 428260),
        position_qty=0.0,
        price=42.99,
        qty=10.0,
        value=429.90000000000003,
        cash=100002.10000000002,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('0f3ab616-6616-4ba5-b32f-8c7f1a6be8cb'),
        order=Order(
            id=UUID('345162e0-5e7b-4e0c-b5bf-dffad0508da9'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 42, 44, 484124),
            filled_at=datetime.datetime(2023, 3, 24, 19, 49, 6, 219276),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.98,
            side=OrderSide.BUY,
            limit_price=42.98
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 49, 6, 219276),
        position_qty=10.0,
        price=42.98,
        qty=10.0,
        value=429.79999999999995,
        cash=99572.30000000002,
        pos_avg_price=42.98
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('53e0171c-6246-40ee-9dd8-f9155be32f11'),
        order=Order(
            id=UUID('826b174d-c894-4c7b-a25e-b42b23eaabad'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 49, 6, 265276),
            filled_at=datetime.datetime(2023, 3, 24, 19, 49, 57, 528455),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=43.005,
            side=OrderSide.SELL,
            limit_price=43.0
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 49, 57, 528455),
        position_qty=0.0,
        price=43.005,
        qty=10.0,
        value=430.05,
        cash=100002.35000000002,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('d827dc6f-51e2-4149-acd8-e438a271fa75'),
        order=Order(
            id=UUID('d931a776-2739-41ba-bd16-d9b45dff59ec'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 52, 1, 100351),
            filled_at=datetime.datetime(2023, 3, 24, 19, 52, 7, 321771),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.94,
            side=OrderSide.BUY,
            limit_price=42.94
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 52, 7, 321771),
        position_qty=10.0,
        price=42.94,
        qty=10.0,
        value=429.4,
        cash=99572.95000000003,
        pos_avg_price=42.94
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('20d15c7a-23c0-4815-85df-8a302e2e0f39'),
        order=Order(
            id=UUID('0419ba73-ad51-4df6-b211-ac4c42a6e032'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 28, 43, 668847),
            filled_at=datetime.datetime(2023, 3, 24, 19, 52, 41, 652899),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.9,
            side=OrderSide.BUY,
            limit_price=42.9
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 52, 41, 652899),
        position_qty=20.0,
        price=42.9,
        qty=10.0,
        value=429.0,
        cash=99143.95000000003,
        pos_avg_price=42.92
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('a2f8bc9b-d2ad-4a0a-a5f3-2cc728d2e541'),
        order=Order(
            id=UUID('36d89e04-fdfc-410d-9608-fa6517a3034d'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 54, 43, 440852),
            filled_at=datetime.datetime(2023, 3, 24, 19, 54, 49, 709012),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.87,
            side=OrderSide.BUY,
            limit_price=42.87
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 54, 49, 709012),
        position_qty=30.0,
        price=42.87,
        qty=10.0,
        value=428.7,
        cash=98715.25000000003,
        pos_avg_price=42.903333333333336
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('dace8d0b-6618-498c-aaea-7d6e43903c92'),
        order=Order(
            id=UUID('57222023-d25e-461b-811a-1abc87390971'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 54, 49, 755012),
            filled_at=datetime.datetime(2023, 3, 24, 19, 55, 45, 671150),
            canceled_at=None,
            symbol='C',
            qty=30,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=30,
            filled_avg_price=42.92,
            side=OrderSide.SELL,
            limit_price=42.92
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 55, 45, 671150),
        position_qty=0.0,
        price=42.92,
        qty=30.0,
        value=1287.6000000000001,
        cash=100002.85000000003,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('3ce200d5-3e8d-4af8-818d-41e3f49e91f9'),
        order=Order(
            id=UUID('09ada304-3920-4d21-a7c5-520116f60161'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 8, 3, 126555),
            filled_at=datetime.datetime(2023, 3, 24, 19, 59, 28, 62458),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.83,
            side=OrderSide.BUY,
            limit_price=42.83
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 59, 28, 62458),
        position_qty=10.0,
        price=42.83,
        qty=10.0,
        value=428.29999999999995,
        cash=99574.55000000003,
        pos_avg_price=42.83
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('51b1ef83-e486-44a1-9809-fd5ebca18a50'),
        order=Order(
            id=UUID('c8894c95-83bc-455e-8501-6622e74ad267'),
            submitted_at=datetime.datetime(2023, 3, 24, 19, 59, 28, 108458),
            filled_at=datetime.datetime(2023, 3, 24, 19, 59, 40, 517988),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.85,
            side=OrderSide.SELL,
            limit_price=42.85
        ),
        timestamp=datetime.datetime(2023, 3, 24, 19, 59, 40, 517988),
        position_qty=0.0,
        price=42.85,
        qty=10.0,
        value=428.5,
        cash=100003.05000000003,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('1a0724f7-53de-42e3-9917-b65ecca4e7a0'),
        order=Order(
            id=UUID('14783679-6871-496c-8875-60c3d6ae0135'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 0, 21, 449585),
            filled_at=datetime.datetime(2023, 3, 24, 20, 0, 25, 189635),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.84,
            side=OrderSide.BUY,
            limit_price=42.84
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 0, 25, 189635),
        position_qty=10.0,
        price=42.84,
        qty=10.0,
        value=428.40000000000003,
        cash=99574.65000000004,
        pos_avg_price=42.84
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('087b5b76-0cc5-4462-971b-782fe4c4c6ad'),
        order=Order(
            id=UUID('3b5bf7fb-cba2-4bfb-b3b7-74e191caf928'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 0, 25, 235635),
            filled_at=datetime.datetime(2023, 3, 24, 20, 1, 49, 107372),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.86,
            side=OrderSide.SELL,
            limit_price=42.86
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 1, 49, 107372),
        position_qty=0.0,
        price=42.86,
        qty=10.0,
        value=428.6,
        cash=100003.25000000004,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('0302b8e0-d427-4f93-9b23-ee1da32149bd'),
        order=Order(
            id=UUID('446f4bab-3bd7-4bbb-ba9b-1d0445cc6371'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 8, 0, 534518),
            filled_at=datetime.datetime(2023, 3, 24, 20, 8, 18, 36437),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.83,
            side=OrderSide.BUY,
            limit_price=42.83
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 8, 18, 36437),
        position_qty=10.0,
        price=42.83,
        qty=10.0,
        value=428.29999999999995,
        cash=99574.95000000004,
        pos_avg_price=42.83
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('1c191c3f-fe56-4486-92f2-b4ab2e0d1d24'),
        order=Order(
            id=UUID('cb920785-4520-44e5-b6af-978da3927c59'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 10, 41, 294273),
            filled_at=datetime.datetime(2023, 3, 24, 20, 10, 45, 568943),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.78,
            side=OrderSide.BUY,
            limit_price=42.78
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 10, 45, 568943),
        position_qty=20.0,
        price=42.78,
        qty=10.0,
        value=427.8,
        cash=99147.15000000004,
        pos_avg_price=42.80499999999999
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('ec034230-58ba-4300-82c1-7d30399d1be0'),
        order=Order(
            id=UUID('f111ec92-77d2-4e38-b789-90d6ed471c76'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 10, 45, 614943),
            filled_at=datetime.datetime(2023, 3, 24, 20, 11, 12, 853893),
            canceled_at=None,
            symbol='C',
            qty=20,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=20,
            filled_avg_price=42.82,
            side=OrderSide.SELL,
            limit_price=42.82
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 11, 12, 853893),
        position_qty=0.0,
        price=42.82,
        qty=20.0,
        value=856.4,
        cash=100003.55000000003,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('2343a817-dcd9-42a5-8645-bf9e9fcb41a2'),
        order=Order(
            id=UUID('24f0e7a7-b1ce-42b6-9514-8721b240b31d'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 14, 40, 530031),
            filled_at=datetime.datetime(2023, 3, 24, 20, 14, 57, 348700),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.74,
            side=OrderSide.BUY,
            limit_price=42.74
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 14, 57, 348700),
        position_qty=10.0,
        price=42.74,
        qty=10.0,
        value=427.40000000000003,
        cash=99576.15000000004,
        pos_avg_price=42.74
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('57f57435-ff77-4e6f-96d6-b29b725c4693'),
        order=Order(
            id=UUID('b8470e7b-6773-47bb-984c-ab44832b3b3b'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 14, 57, 394700),
            filled_at=datetime.datetime(2023, 3, 24, 20, 15, 12, 621144),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.76,
            side=OrderSide.SELL,
            limit_price=42.76
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 15, 12, 621144),
        position_qty=0.0,
        price=42.76,
        qty=10.0,
        value=427.59999999999997,
        cash=100003.75000000004,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('069b4a2d-0377-4345-96b6-74e9fae89d9e'),
        order=Order(
            id=UUID('9a4bbe02-fc9e-4261-95d3-d609737662a9'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 25, 41, 185936),
            filled_at=datetime.datetime(2023, 3, 24, 20, 27, 34, 90412),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.86,
            side=OrderSide.BUY,
            limit_price=42.86
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 27, 34, 90412),
        position_qty=10.0,
        price=42.86,
        qty=10.0,
        value=428.6,
        cash=99575.15000000004,
        pos_avg_price=42.86
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('6bdd0e17-b1c2-4080-8f26-c980d615f31f'),
        order=Order(
            id=UUID('070c371c-f8d4-4437-b42f-6a94d3962d7b'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 27, 34, 136412),
            filled_at=datetime.datetime(2023, 3, 24, 20, 28, 24, 695266),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.88,
            side=OrderSide.SELL,
            limit_price=42.88
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 28, 24, 695266),
        position_qty=0.0,
        price=42.88,
        qty=10.0,
        value=428.8,
        cash=100003.95000000004,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('303bbd02-4d8b-4940-9878-52c1dca92c73'),
        order=Order(
            id=UUID('247f87b0-4d97-4527-bcf1-2e0679c546b0'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 35, 0, 150590),
            filled_at=datetime.datetime(2023, 3, 24, 20, 35, 23, 954682),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.9,
            side=OrderSide.BUY,
            limit_price=42.9
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 35, 23, 954682),
        position_qty=10.0,
        price=42.9,
        qty=10.0,
        value=429.0,
        cash=99574.95000000004,
        pos_avg_price=42.9
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('697ed9c5-40c3-439c-9811-29c9f4d74487'),
        order=Order(
            id=UUID('3ce9a256-059e-43ed-a290-286fa310fa21'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 35, 24, 682),
            filled_at=datetime.datetime(2023, 3, 24, 20, 36, 15, 43220),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.92,
            side=OrderSide.SELL,
            limit_price=42.92
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 36, 15, 43220),
        position_qty=0.0,
        price=42.92,
        qty=10.0,
        value=429.20000000000005,
        cash=100004.15000000004,
        pos_avg_price=0.0
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('e0a33f84-91d1-4e89-95d9-e95a3a90b0fb'),
        order=Order(
            id=UUID('2889c4db-7c12-4b17-b35f-c81f53625c71'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 48, 0, 466959),
            filled_at=datetime.datetime(2023, 3, 24, 20, 48, 0, 901059),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.91,
            side=OrderSide.BUY,
            limit_price=42.91
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 48, 0, 901059),
        position_qty=10.0,
        price=42.91,
        qty=10.0,
        value=429.09999999999997,
        cash=99575.05000000003,
        pos_avg_price=42.91
    ),
    TradeUpdate(
        event=TradeEvent.FILL,
        execution_id=UUID('bca37e22-3ec2-4cf4-9ce8-779675469324'),
        order=Order(
            id=UUID('65a65038-7cda-4b18-aa5b-c48af539d1ba'),
            submitted_at=datetime.datetime(2023, 3, 24, 20, 48, 0, 947059),
            filled_at=datetime.datetime(2023, 3, 24, 20, 48, 55, 262008),
            canceled_at=None,
            symbol='C',
            qty=10,
            status=OrderStatus.FILLED,
            order_type=OrderType.LIMIT,
            filled_qty=10,
            filled_avg_price=42.93,
            side=OrderSide.SELL,
            limit_price=42.93
        ),
        timestamp=datetime.datetime(2023, 3, 24, 20, 48, 55, 262008),
        position_qty=0.0,
        price=42.93,
        qty=10.0,
        value=429.3,
        cash=100004.35000000003,
        pos_avg_price=0.0
    )
]

#create pandas
trade_dict = AttributeDict(orderid=[],timestamp=[],symbol=[],side=[],order_type=[],qty=[],price=[],position_qty=[],value=[],cash=[],pos_avg_price=[])
for t in tradeList:
    if t.event == TradeEvent.FILL:
        trade_dict.orderid.append(str(t.order.id))
        trade_dict.timestamp.append(t.timestamp)
        trade_dict.symbol.append(t.order.symbol)
        trade_dict.side.append(t.order.side)
        trade_dict.qty.append(int(t.qty))
        trade_dict.price.append(t.price)
        trade_dict.position_qty.append(int(t.position_qty))
        trade_dict.value.append(t.value)
        trade_dict.cash.append(t.cash)
        trade_dict.order_type.append(t.order.order_type)
        trade_dict.pos_avg_price.append(t.pos_avg_price)

trade_df = pd.DataFrame(trade_dict)
trade_df = trade_df.set_index('timestamp',drop=False)

#max positions- 
max_positions = trade_df.groupby('side')['qty'].value_counts().reset_index(name='count').sort_values(['qty'], ascending=False)
max_positions = max_positions[max_positions['side'] == OrderSide.SELL]
max_positions = max_positions.drop(columns=['side'], axis=1)

#filt = max_positions['side'] == 'OrderSide.BUY'
res = dict(zip(max_positions['qty'], max_positions['count']))

ouput_dict=dict(maxpos=str(res))

all_summary = trade_df.describe(include='all')
print(all_summary)

print(ouput_dict)
#a = trade_df.value_counts(subset=['position_qty'])
#print(max_positions.to_dict('records'))
#print(max_positions.to_dict('list'))
#print(trade_df.describe(include='max_positions'))