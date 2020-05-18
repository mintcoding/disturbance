import re
import traceback
import os
import base64
import geojson
import json
from six.moves.urllib.parse import urlparse
from wsgiref.util import FileWrapper
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics, views
from rest_framework.decorators import detail_route, list_route, renderer_classes, parser_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from collections import OrderedDict
from django.core.cache import cache
from ledger.accounts.models import EmailUser, Address
from ledger.address.models import Country
from datetime import datetime, timedelta, date
from disturbance.components.proposals.utils import save_proponent_data,save_assessor_data, proposal_submit_apiary
from disturbance.components.proposals.models import searchKeyWords, search_reference, ProposalUserAction, \
    ProposalApiarySiteLocation, OnSiteInformation
from disturbance.utils import missing_required_fields, search_tenure
from disturbance.components.main.utils import check_db_connection

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from disturbance.components.main.models import Document, Region, District, Tenure, ApplicationType
from disturbance.components.proposals.models import (
    ProposalType,
    Proposal,
    ProposalDocument,
    Referral,
    ProposalRequirement,
    ProposalStandardRequirement,
    AmendmentRequest,
    AmendmentReason,
    AmendmentRequestDocument,
    ApiaryReferralGroup,
    ApiaryProposal,
)
from disturbance.components.proposals.serializers import (
    SendReferralSerializer,
    ProposalTypeSerializer,
    ProposalSerializer,
    InternalProposalSerializer,
    SaveProposalSerializer,
    DTProposalSerializer,
    ProposalUserActionSerializer,
    ProposalLogEntrySerializer,
    DTReferralSerializer,
    ReferralSerializer,
    ReferralProposalSerializer,
    ProposalRequirementSerializer,
    ProposalStandardRequirementSerializer,
    ProposedApprovalSerializer,
    PropedDeclineSerializer,
    AmendmentRequestSerializer,
    SearchReferenceSerializer,
    SearchKeywordSerializer,
    ListProposalSerializer,
    AmendmentRequestDisplaySerializer,
    SaveProposalRegionSerializer,
)
from disturbance.components.proposals.serializers_base import ProposalReferralSerializer
from disturbance.components.proposals.serializers_apiary import (
    ProposalApiarySerializer,
    InternalProposalApiarySerializer,
    ProposalApiarySiteLocationSerializer,
    ProposalApiaryTemporaryUseSerializer,
    ProposalApiarySiteTransferSerializer, 
    OnSiteInformationSerializer,
    ApiaryReferralGroupSerializer,
    SaveApiaryProposalSerializer,
)
from disturbance.components.approvals.models import Approval
from disturbance.components.approvals.serializers import ApprovalSerializer
from disturbance.components.compliances.models import Compliance
from disturbance.components.compliances.serializers import ComplianceSerializer

from disturbance.helpers import is_customer, is_internal
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer
from rest_framework.filters import BaseFilterBackend

import logging
logger = logging.getLogger(__name__)


class ProposalApiarySiteLocationViewSet(viewsets.ModelViewSet):
    queryset = ProposalApiarySiteLocation.objects.none()
    serializer_class = ProposalApiarySiteLocationSerializer

    @detail_route(methods=['GET', ])
    def on_site_information_list(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ProposalApiarySiteLocationSerializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return ProposalApiarySiteLocation.objects.all()


class ApiaryReferralGroupViewSet(viewsets.ModelViewSet):
    queryset = ApiaryReferralGroup.objects.none()
    serializer_class = ApiaryReferralGroupSerializer

    def get_queryset(self):
        #user = self.request.user
        #import ipdb; ipdb.set_trace()
        if is_internal(self.request): #user.is_authenticated():
            return ApiaryReferralGroup.objects.all()
        else:
            return ApiaryReferralGroup.objects.none()


class ApiaryProposalViewSet(viewsets.ModelViewSet):
    queryset = ApiaryProposal.objects.none()
    serializer_class = ProposalApiarySerializer

    def get_queryset(self):
        #user = self.request.user
        #import ipdb; ipdb.set_trace()
        if is_internal(self.request): #user.is_authenticated():
            return ApiaryProposal.objects.all()
        else:
            return ApiaryProposal.objects.none()

    def create(self, request, *args, **kwargs):
        try:
            http_status = status.HTTP_200_OK
            #application_type = ApplicationType.objects.get(id=request.data.get('application'))
            application_type = ApplicationType.objects.get(name=ApplicationType.Apiary)

            #region = request.data.get('region') if request.data.get('region') else 1
            #region = request.data.get('region')
            #district = request.data.get('district')
            #activity = request.data.get('activity')
            #sub_activity1 = request.data.get('sub_activity1')
            #sub_activity2 = request.data.get('sub_activity2')
            # TODO: still required?
            category = request.data.get('category')
            approval_level = request.data.get('approval_level')

            # Get most recent versions of the Proposal Types
            qs_proposal_type = ProposalType.objects.all().order_by('name', '-version').distinct('name')
            proposal_type = qs_proposal_type.get(name=application_type.name)
            applicant = None
            proxy_applicant = None
            if request.data.get('behalf_of') == 'individual':
                proxy_applicant = request.user.id
            else:
                applicant = request.data.get('behalf_of')

            data = {
                #'schema': qs_proposal_type.order_by('-version').first().schema,
                'schema': proposal_type.schema,
                'submitter': request.user.id,
                'applicant': applicant,
                'proxy_applicant': proxy_applicant,
                'application_type': application_type.id,
                #'region': region,
                #'district': district,
                #'activity': activity,
                'approval_level': approval_level,
                #'sub_activity_level1':sub_activity1,
                #'sub_activity_level2':sub_activity2,
                'management_area':category,
                'data': [
                ],
            }
            serializer = SaveApiaryProposalSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance=serializer.save()

            details_data={
                'proposal': instance.id
            }

            serializer=ProposalApiarySiteLocationSerializer(data=details_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer=ProposalApiaryTemporaryUseSerializer(data=details_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer=ProposalApiarySiteTransferSerializer(data=details_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer = SaveApiaryProposalSerializer(instance)
            #import ipdb; ipdb.set_trace()
            return Response(serializer.data)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update(self, request, *args, **kwargs):
        try:
            http_status = status.HTTP_200_OK
            instance = self.get_object()
            serializer = SaveApiaryProposalSerializer(instance,data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def destroy(self, request,*args,**kwargs):
        try:
            http_status = status.HTTP_200_OK
            instance = self.get_object()
            serializer = SaveApiaryProposalSerializer(instance,{'processing_status':'discarded', 'previous_application': None},partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data,status=http_status)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def submit(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            save_proponent_data(instance, request, self)
            proposal_submit_apiary(instance, request)
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
            #return redirect(reverse('external'))
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                raise serializers.ValidationError(repr(e[0].encode('utf-8')))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

