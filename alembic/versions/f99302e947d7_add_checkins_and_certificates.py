"""add checkins and certificates"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f99302e947d7"
down_revision: Union[str, Sequence[str], None] = "18102d3534b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registration_id", sa.Integer(), nullable=False),
        sa.Column("check_in_time", sa.DateTime(), nullable=False),
        sa.Column("check_out_time", sa.DateTime(), nullable=True),
        sa.Column(
            "check_in_method",
            sa.Enum(
                "QR_CODE",
                "MANUAL",
                "STAFF",
                name="checkinmethod",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["registration_id"],
            ["registrations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registration_id"),
    )

    op.create_index(
        "ix_checkins_id",
        "checkins",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_checkins_registration_id",
        "checkins",
        ["registration_id"],
        unique=True,
    )

    op.create_table(
        "certificates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "certificate_number",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column("attendee_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column(
            "certificate_type",
            sa.Enum(
                "PARTICIPATION",
                "COMPLETION",
                name="certificatetype",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "ISSUED",
                "REVOKED",
                name="certificatestatus",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["attendee_id"],
            ["attendees.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("certificate_number"),
    )

    op.create_index(
        "ix_certificates_id",
        "certificates",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_certificates_certificate_number",
        "certificates",
        ["certificate_number"],
        unique=True,
    )

    op.create_index(
        "ix_certificates_attendee_id",
        "certificates",
        ["attendee_id"],
        unique=False,
    )

    op.create_index(
        "ix_certificates_event_id",
        "certificates",
        ["event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_certificates_event_id",
        table_name="certificates",
    )
    op.drop_index(
        "ix_certificates_attendee_id",
        table_name="certificates",
    )
    op.drop_index(
        "ix_certificates_certificate_number",
        table_name="certificates",
    )
    op.drop_index(
        "ix_certificates_id",
        table_name="certificates",
    )
    op.drop_table("certificates")

    op.drop_index(
        "ix_checkins_registration_id",
        table_name="checkins",
    )
    op.drop_index(
        "ix_checkins_id",
        table_name="checkins",
    )
    op.drop_table("checkins")
