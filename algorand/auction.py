from algosdk.future import transaction
from pyteal import *

from .contracts import deploy_app


def approval_program() -> str:
    """Return the PyTeal approval program for a basic auction."""
    seller = Bytes("seller")
    asset = Bytes("asset_id")
    start = Bytes("start")
    end = Bytes("end")
    reserve = Bytes("reserve")
    highest_bid = Bytes("highest_bid")
    highest_bidder = Bytes("highest_bidder")
    closed = Bytes("closed")

    on_create = Seq(
        Assert(Txn.application_args.length() == Int(4)),
        App.globalPut(seller, Txn.sender()),
        App.globalPut(asset, Btoi(Txn.application_args[0])),
        App.globalPut(start, Btoi(Txn.application_args[1])),
        App.globalPut(end, Btoi(Txn.application_args[2])),
        App.globalPut(reserve, Btoi(Txn.application_args[3])),
        App.globalPut(highest_bid, Int(0)),
        App.globalPut(highest_bidder, Global.zero_address()),
        App.globalPut(closed, Int(0)),
        Approve(),
    )

    bid_payment = Gtxn[0]

    refund_prev = Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(highest_bidder),
                TxnField.amount: App.globalGet(highest_bid),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )

    on_bid = Seq(
        Assert(App.globalGet(closed) == Int(0)),
        Assert(Global.latest_timestamp() >= App.globalGet(start)),
        Assert(Global.latest_timestamp() < App.globalGet(end)),
        Assert(bid_payment.type_enum() == TxnType.Payment),
        Assert(bid_payment.sender() == Txn.sender()),
        Assert(bid_payment.receiver() == Global.current_application_address()),
        Assert(bid_payment.amount() > App.globalGet(highest_bid)),
        Assert(bid_payment.amount() >= App.globalGet(reserve)),
        If(App.globalGet(highest_bid) > Int(0)).Then(refund_prev),
        App.globalPut(highest_bid, bid_payment.amount()),
        App.globalPut(highest_bidder, Txn.sender()),
        Approve(),
    )

    on_claim = Seq(
        Assert(App.globalGet(closed) == Int(0)),
        Assert(Global.latest_timestamp() >= App.globalGet(end)),
        Assert(Txn.sender() == App.globalGet(highest_bidder)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(asset),
                TxnField.asset_receiver: App.globalGet(highest_bidder),
                TxnField.asset_amount: Int(1),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(seller),
                TxnField.amount: App.globalGet(highest_bid),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
        App.globalPut(closed, Int(1)),
        Approve(),
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, Cond([
            Txn.application_args[0] == Bytes("bid"), on_bid
        ], [
            Txn.application_args[0] == Bytes("claim"), on_claim
        ])],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Txn.sender() == App.globalGet(seller))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Txn.sender() == App.globalGet(seller))],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
    )

    return compileTeal(program, mode=Mode.Application, version=7)


def clear_program() -> str:
    """Clear state program that always approves."""
    return compileTeal(Approve(), mode=Mode.Application, version=7)


def deploy_auction_app(private_key: str, asset_id: int, start: int, end: int, reserve: int) -> str:
    """Deploy the auction contract to the blockchain and return the transaction ID."""
    app_args = [
        asset_id.to_bytes(8, "big"),
        start.to_bytes(8, "big"),
        end.to_bytes(8, "big"),
        reserve.to_bytes(8, "big"),
    ]
    global_schema = transaction.StateSchema(7, 2)
    return deploy_app(
        private_key,
        approval_program(),
        clear_program(),
        global_schema=global_schema,
        local_schema=transaction.StateSchema(0, 0),
        app_args=app_args,
    )
