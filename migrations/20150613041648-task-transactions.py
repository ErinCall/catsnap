step(
    """
        create table task_transaction (
            transaction_id uuid primary key
        )
    """,
    """
        drop table task_transaction
    """
)
