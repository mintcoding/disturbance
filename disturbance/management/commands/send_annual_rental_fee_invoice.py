import datetime
from decimal import Decimal

import pytz
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
import logging

from django.db import transaction
from django.db.models import Q, Min
from ledger.settings_base import TIME_ZONE

from disturbance.components.approvals.email import send_annual_rental_fee_awaiting_payment_confirmation
from disturbance.components.approvals.models import Approval
from disturbance.components.das_payments.models import AnnualRentalFee, AnnualRentalFeePeriod, AnnualRentalFeeApiarySite
from disturbance.components.das_payments.utils import create_other_invoice_for_annual_rental_fee, \
    generate_line_items_for_annual_rental_fee
from disturbance.components.proposals.models import ApiaryAnnualRentalFeeRunDate, ApiaryAnnualRentalFeePeriodStartDate, \
    ApiarySite

logger = logging.getLogger(__name__)


def get_annual_rental_fee_period(target_date):
    """
    Retrieve the annual rental fee period, the invoice for this period should have been issued on the target_date passed as a parameter
    """
    target_date_year = target_date.year

    # Calculate cron job period
    run_date = ApiaryAnnualRentalFeeRunDate.objects.get(name=ApiaryAnnualRentalFeeRunDate.NAME_CRON)
    run_date_month = run_date.date_run_cron.month
    run_date_day = run_date.date_run_cron.day

    # Calculate the run_date in the year where the target_date is in
    prev_run_date = datetime.date(year=target_date_year, month=run_date_month, day=run_date_day)
    if prev_run_date > target_date:
        # prev_run_date calculated above is in the future.  Calculate one before that
        prev_run_date = datetime.date(year=prev_run_date.year-1, month=prev_run_date.month, day=prev_run_date.day)

    # Calculate annual rental fee period
    # annual rental fee start date must be between the prev_run_date and next_run_date
    start_date = ApiaryAnnualRentalFeePeriodStartDate.objects.get(name=ApiaryAnnualRentalFeePeriodStartDate.NAME_PERIOD_START)
    period_start_date_month = start_date.period_start_date.month
    period_start_date_day = start_date.period_start_date.day

    # Calculate the period start date in the year where the prev_run_date is in
    period_start_date = datetime.date(year=prev_run_date.year, month=period_start_date_month, day=period_start_date_day)
    if period_start_date < prev_run_date:
        # period_start_date calculated above is before the previous cron job run date.  Calculate the next one
        period_start_date = datetime.date(year=period_start_date.year+1, month=period_start_date.month, day=period_start_date.day)

    period_end_date = datetime.date(year=period_start_date.year+1, month=period_start_date.month, day=period_start_date.day) - datetime.timedelta(days=1)

    return period_start_date, period_end_date


def get_approvals(annual_rental_fee_period):
    # Retrieve the licences which will be valid within this period and no invoices have been issued for this period
    q_objects = Q()
    q_objects &= Q(apiary_approval=True)
    q_objects &= Q(expiry_date__gte=annual_rental_fee_period.period_start_date)
    q_objects &= Q(status=Approval.STATUS_CURRENT)

    approval_qs = Approval.objects.filter(q_objects).exclude(
        # We don't want to send an invoice for the same period
        annual_rental_fees__in=AnnualRentalFee.objects.filter(annual_rental_fee_period=annual_rental_fee_period)
    )

    return approval_qs


def get_apiary_sites_to_be_charged(approval, annual_rental_fee_period):
    # 1. Retrieve all the annual_rental_fees under this approval and this annual_rental_fee_period
    #       annual_rental_fees = AnnualRentalFee.objects.filter(approval=approval, annual_rental_fee_period=annual_rental_fee_period)
    # 2. Retrieve all the current apiary_sites under this approval
    #       sites_status_current = approval.apiary_sites.filter(status=ApiarySite.STATUS_CURRENT)
    # 3. Retrieve apiary_sites which invoices have been issued for already
    #       annual_rental_fee_apiary_sites = AnnualRentalFeeApiarySite.objects.filter(apiary_site__in=sites_status_current, annual_rental_fee__in=annual_rental_fees)
    #       sites_exclude = ApiarySite.objects.filter(annualrentalfeeapiarysite__in=annual_rental_fee_apiary_sites)

    # Combine the queries above
    apiary_sites = approval.apiary_sites.filter(
        # ApiarySite must be the 'current' status
        status=ApiarySite.STATUS_CURRENT
    ).exclude(
        # Exclude the apiaries for which the invoices have been issued for this period
        annualrentalfeeapiarysite__in=AnnualRentalFeeApiarySite.objects.filter(
            annual_rental_fee__in=AnnualRentalFee.objects.filter(
                approval=approval,
                annual_rental_fee_period=annual_rental_fee_period
            )
        )
    )
    return apiary_sites


class Command(BaseCommand):
    help = 'Send annual rent fee invoices for the apiary'

    def handle(self, *args, **options):
        try:
            # Determine the start and end date of the annual rental fee, for which the invoices should be issued
            today_now_local = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            today_date_local = today_now_local.date()
            period_start_date, period_end_date = get_annual_rental_fee_period(today_date_local)

            # Retrieve annual rental fee period object for the period calculated above
            # This period should not overwrap the existings, otherwise you will need a refund
            annual_rental_fee_period, created = AnnualRentalFeePeriod.objects.get_or_create(period_start_date=period_start_date, period_end_date=period_end_date)

            # Retrieve the licences which will be valid within the current annual rental fee period
            approval_qs = get_approvals(annual_rental_fee_period)

            # Issue the annual rental fee invoices per approval per annual_rental_fee_period
            for approval in approval_qs:
                try:
                    with transaction.atomic():
                        apiary_sites_to_be_charged = get_apiary_sites_to_be_charged(approval, annual_rental_fee_period)

                        if apiary_sites_to_be_charged.count() > 0:
                            # invoice, details_dict = create_other_invoice_for_annual_rental_fee(approval, today_now_local, (period_start_date, period_end_date), apiary_sites_to_be_charged)
                            products, details_dict = generate_line_items_for_annual_rental_fee(approval, today_now_local, (period_start_date, period_end_date), apiary_sites_to_be_charged)

                            products = make_serializable(products)  # Make line items serializable to store in the JSONField

                            annual_rental_fee = AnnualRentalFee.objects.create(
                                approval=approval,
                                annual_rental_fee_period=annual_rental_fee_period,
                                # invoice_reference=invoice.reference,  #  We don't create an ledger invoice, but just store the lines
                                invoice_period_start_date=details_dict['charge_start_date'],
                                invoice_period_end_date=details_dict['charge_end_date'],
                                lines=products,  # This is used when generating the invoice at payment time
                            )

                            # Store the apiary sites which the invoice created above has been issued for
                            for apiary_site in apiary_sites_to_be_charged:
                                annual_rental_fee_apiary_site = AnnualRentalFeeApiarySite(apiary_site=apiary_site, annual_rental_fee=annual_rental_fee)
                                annual_rental_fee_apiary_site.save()

                            # TODO: Attach the invoice and send emails
                            #   update invoice_sent attribute of the annual_rental_fee obj?
                            email_data = send_annual_rental_fee_awaiting_payment_confirmation(approval, annual_rental_fee)

                            # TODO: Add comms log

                except Exception as e:
                    logger.error('Error command {}'.format(__name__))
                    logger.error('Failed to send an annual rental fee invoice for the approval {}'.format(approval.lodgement_number))

        except Exception as e:
            logger.error('Error command {}'.format(__name__))


def make_serializable(line_items):
    for line in line_items:
        for key in line:
            if isinstance(line[key], Decimal):
                # Convert Decimal to str
                line[key] = str(line[key])
    return line_items
