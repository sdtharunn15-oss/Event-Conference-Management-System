from logging.config import fileConfig
from app.models.feedback import Feedback
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.database import Base

from app.models.user import User, RefreshToken
from app.models.event import Event
from app.models.venue import Venue
from app.models.hall import Hall
from app.models.speaker import Speaker
from app.models.attendee import Attendee
from app.models.registration import Registration
from app.models.ticket import Ticket
from app.models.ticket_purchase import TicketPurchase
from app.models.payment import Payment
from app.models.session import Session
from app.models.checkin import CheckIn
from app.models.certificate import Certificate
from app.models.notification import Notification


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("%", "%%"),
)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
