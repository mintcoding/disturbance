import pytz
from django.conf import settings
from datetime import datetime, timedelta, date

from django.contrib.gis.measure import Distance
from django.db.models import Q

from ledger.settings_base import TIME_ZONE
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from disturbance.components.main.fields import CustomChoiceField
from disturbance.components.organisations.serializers import OrganisationSerializer
from disturbance.components.organisations.models import UserDelegation
from disturbance.components.proposals.serializers_base import (
        BaseProposalSerializer, 
        #ProposalReferralSerializer,
        ProposalDeclinedDetailsSerializer,
        EmailUserSerializer,
        )
from disturbance.components.proposals.models import (
    Proposal,
    ProposalApiary,
    ProposalApiaryTemporaryUse,
    ProposalApiarySiteTransfer,
    ApiaryChecklistQuestion,
    ApiaryChecklistAnswer,
    ProposalApiaryDocument,
    ApiarySite,
    OnSiteInformation,
    ApiaryReferralGroup,
    TemporaryUseApiarySite,
    SiteTransferApiarySite,
    ApiaryReferral,
    Referral, 
    ApiarySiteFeeType, 
    ApiarySiteFeeRemainder, 
    SiteCategory,
    ProposalRequirement,
    )
from disturbance.components.approvals.models import (
        Approval,
        )

from rest_framework import serializers
from ledger.accounts.models import Address
from reversion.models import Version
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from ledger.accounts.models import EmailUser

from disturbance.settings import RESTRICTED_RADIUS


class VersionSerializer(serializers.ModelSerializer):
    #serializable_value = serializers.JSONField()
    proposal_fields = serializers.SerializerMethodField()
    date_modified = serializers.SerializerMethodField()
    class Meta:
        model = Version
        #fields = '__all__'
        fields = (
                'id',
                'revision',
                'proposal_fields',
                'date_modified',
                )
        read_only_fields = (
                'id',
                'revision',
                'proposal_fields',
                'date_modified',
                )

    def get_date_modified(self, obj):
        date_modified = None
        if obj.revision and obj.revision.date_created:
            date_modified = timezone.localtime(obj.revision.date_created)
        return date_modified

    def get_proposal_fields(self, obj):
        proposal_data = []
        if obj.revision:
            apiary_sites = []
            for record in obj.revision.version_set.all():
                if record.object:
                    # Exclude these models from the result
                    if record.object._meta.model_name in [
                            'proposallogentry',
                            'annualrentalfee',
                            'approvaldocument',
                            'approval',
                            ]:
                        continue
                    elif ContentType.objects.get(id=record.content_type_id).model == 'apiarysite':
                        payload = record.field_dict
                        # Exclude these fields from the result
                        payload.pop("wkb_geometry", None)
                        payload.pop("objects", None)
                        payload.pop("site_guid", None)
                        apiary_sites.append({record.object._meta.model_name: payload})
                    else:
                        #print("record.object._meta.model_name")
                        #print(record.object._meta.model_name)
                        proposal_data.append({record.object._meta.model_name: record.field_dict})
            proposal_data.append({'apiary_sites': apiary_sites})
        #print("proposal_data")
        #print(proposal_data)
        return proposal_data


class ProposalHistorySerializer(serializers.ModelSerializer):
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'versions',
                )

    def get_versions(self, obj):
        entry_versions = VersionSerializer(
                Version.objects.get_for_object(obj),
                many=True)
        return entry_versions.data


class ApiaryChecklistQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiaryChecklistQuestion
        fields=('id',
                'text',
                'answer_type',
                'checklist_type',
                'order'
                )

class ApiaryChecklistAnswerSerializer(serializers.ModelSerializer):
    question = ApiaryChecklistQuestionSerializer()

    class Meta:
        model = ApiaryChecklistAnswer
        fields=('id',
                'question',
                'answer',
                'proposal_id',
                )

class ApplicantAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id',
            'line1',
            'line2',
            'line3',
            'locality',
            'state',
            'country',
            'postcode'
        )


class ApiarySiteOptimisedSerializer(serializers.ModelSerializer):
    proposal_apiary_id = serializers.IntegerField(write_only=True,)
    site_category_id = serializers.IntegerField(write_only=True,)
    coordinates = serializers.SerializerMethodField()

    def get_coordinates(self, apiary_site):
        try:
            return {'lng': apiary_site.wkb_geometry.x, 'lat': apiary_site.wkb_geometry.y}
        except:
            return {'lng': '', 'lat': ''}

    class Meta:
        model = ApiarySite
        fields = (
            'id',
            'available',
            'site_guid',
            'proposal_apiary_id',
            'site_category_id',
            'coordinates',
            'status'
        )


class OnSiteInformationSerializer(serializers.ModelSerializer):
    apiary_site_id = serializers.IntegerField(required=False)
    apiary_site = ApiarySiteOptimisedSerializer(read_only=True)
    datetime_deleted = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = OnSiteInformation
        fields = (
            'id',
            'apiary_site',
            'apiary_site_id',
            'period_from',
            'period_to',
            'comments',
            'datetime_deleted',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

        if not self.partial:
            if not data['period_from']:
                field_errors['Period from'] = ['Please select a date.',]
            if not data['period_to']:
                field_errors['Period to'] = ['Please select a date.',]
            if not data['apiary_site_id'] and not data['apiary_site_id'] > 0:
                field_errors['Site'] = ['Please select a site',]
            if not data['comments']:
                field_errors['comments'] = ['Please enter comments.',]

            # Raise errors
            if field_errors:
                raise serializers.ValidationError(field_errors)

            if data['period_from'] > data['period_to']:
                non_field_errors.append('Period "from" date must be before "to" date.')

            # Raise errors
            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)
        else:
            # Partial udpate, which means the dict data doesn't have all the field
            pass

        return data


class ApiarySiteSavePointSerializer(GeoFeatureModelSerializer):

    def validate(self, attrs):
        non_field_errors = []

        qs_sites_within = ApiarySite.objects.filter(wkb_geometry__distance_lte=(attrs['wkb_geometry'], Distance(m=RESTRICTED_RADIUS))).\
                                             exclude(status__in=ApiarySite.NON_RESTRICTIVE_STATUSES).exclude(id=self.instance.id)
        if qs_sites_within:
            # There is at least one existing apiary site which is too close to the site being created
            non_field_errors.append('There is an existing apiary site which is too close to the apiary site you are adding at the coordinates: {}'.format(attrs['wkb_geometry'].coords))

        # Raise errors
        if non_field_errors:
            raise serializers.ValidationError(non_field_errors)

        return attrs

    class Meta:
        model = ApiarySite
        geo_field = 'wkb_geometry'
        fields = ('wkb_geometry',)


class ApiarySiteSerializer(serializers.ModelSerializer):
    proposal_apiary_id = serializers.IntegerField(write_only=True, required=False)
    site_category_id = serializers.IntegerField(write_only=True, required=False)
    site_category = serializers.CharField(source='site_category.name', read_only=True)
    onsiteinformation_set = OnSiteInformationSerializer(read_only=True, many=True,)
    coordinates = serializers.SerializerMethodField()
    as_geojson = serializers.SerializerMethodField()
    previous_site_holder_or_applicant = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)

    def validate(self, attrs):
        return attrs

    def get_previous_site_holder_or_applicant(self, apiary_site):
        if apiary_site.approval:
            relevant_applicant_name = apiary_site.approval.relevant_applicant_name
        else:
            relevant_applicant_name = apiary_site.proposal_apiary.proposal.relevant_applicant_name

        return relevant_applicant_name

    def get_as_geojson(self, apiary_site):
        return ApiarySiteGeojsonSerializer(apiary_site).data

    def get_coordinates(self, apiary_site):
        try:
            return {'lng': apiary_site.wkb_geometry.x, 'lat': apiary_site.wkb_geometry.y}
        except:
            return {'lng': '', 'lat': ''}

    class Meta:
        model = ApiarySite
        fields = (
            'id',
            'available',
            # 'temporary_used',
            'site_guid',
            'proposal_apiary_id',
            'site_category_id',
            'site_category',
            'onsiteinformation_set',
            'coordinates',
            'as_geojson',
            'status',
            'workflow_selected_status',
            'previous_site_holder_or_applicant',
        )


class ApiarySiteGeojsonSerializer(GeoFeatureModelSerializer):
    site_category_name = serializers.CharField(source='site_category.name')
    stable_coords = serializers.SerializerMethodField()

    class Meta:
        model = ApiarySite
        geo_field = 'wkb_geometry'

        fields = (
            'id',
            'site_guid',
            'available',
            'wkb_geometry',
            'site_category_name',
            'status',
            'workflow_selected_status',
            'stable_coords',
        )

    def get_stable_coords(self, obj):
        return [obj.wkb_geometry.tuple[0], obj.wkb_geometry.tuple[1]]


class SiteTransferApiarySiteSerializer(serializers.ModelSerializer):
    proposal_apiary_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site = ApiarySiteSerializer(read_only=True)
    # apiary_site_approval = ApiarySiteApprovalSerializer(read_only=True)
    # apiary_site_approval_id = serializers.IntegerField(write_only=True, required=False)
    # apiary_site = serializers.SerializerMethodField()

    def validate(self, attrs):
        # TODO: check if the site is not temporary used to another person for the period
        # TODO: check if the licence is valid, etc
        return attrs

    class Meta:
        model = SiteTransferApiarySite
        fields = (
            'id',
            'proposal_apiary_id',
            # 'apiary_site_approval',
            # 'apiary_site_approval_id',
            'apiary_site_id',
            'apiary_site',
            'customer_selected',
            'internal_selected',
        )


class ProposalApiarySerializer(serializers.ModelSerializer):
    apiary_sites = ApiarySiteSerializer(read_only=True, many=True)
    #site_transfer_apiary_sites = SiteTransferApiarySiteSerializer(read_only=True, many=True)
    transfer_apiary_sites = serializers.SerializerMethodField()
    on_site_information_list = serializers.SerializerMethodField()  # This is used for displaying OnSite table at the frontend

    #checklist_questions = serializers.SerializerMethodField()
    checklist_answers = serializers.SerializerMethodField()
    site_remainders = serializers.SerializerMethodField()
    originating_approval_lodgement_number = serializers.SerializerMethodField()
    #target_approval_id = serializers.SerializerMethodField()
    target_approval_lodgement_number = serializers.SerializerMethodField()
    transferee_name = serializers.SerializerMethodField()
    transferee_org_name = serializers.SerializerMethodField()
    transferee_first_name = serializers.SerializerMethodField()
    transferee_last_name = serializers.SerializerMethodField()

    class Meta:
        model = ProposalApiary
        fields = (
            'id',
            'title',
            'proposal',
            'apiary_sites',
            #'site_transfer_apiary_sites',
            'transfer_apiary_sites',
            'longitude',
            'latitude',
            'on_site_information_list',
            #'checklist_questions',
            'checklist_answers',
            'site_remainders',
            'originating_approval_id',
            'originating_approval_lodgement_number',
            'target_approval_id',
            'target_approval_lodgement_number',
            'transferee_name',
            'transferee_org_name',
            'transferee_first_name',
            'transferee_last_name',
        )

    def get_transfer_apiary_sites(self, obj):
        #import ipdb;ipdb.set_trace()
        sites = None
        if obj.proposal.customer_status == 'draft':
            sites = obj.site_transfer_apiary_sites.all()
        else:
            sites = obj.site_transfer_apiary_sites.filter(customer_selected=True)
        return SiteTransferApiarySiteSerializer(sites, many=True).data

    def get_transferee_name(self, obj):
        name = None
        if obj.proposal.approval:
            name = obj.proposal.approval.relevant_applicant_name
        return name

    def get_transferee_org_name(self, obj):
        name = None
        if obj.proposal.approval and obj.proposal.approval.applicant:
            name = obj.proposal.approval.applicant.name
        return name

    def get_transferee_first_name(self, obj):
        name = None
        if obj.proposal.approval and obj.proposal.approval.proxy_applicant:
            name = obj.proposal.approval.proxy_applicant.first_name
        return name

    def get_transferee_last_name(self, obj):
        name = None
        if obj.proposal.approval and obj.proposal.approval.proxy_applicant:
            name = obj.proposal.approval.proxy_applicant.last_name
        return name

    #def get_target_approval_id(self, obj):
    #    target_id = None
    #    if obj.proposal.approval:
    #        target_id = obj.proposal.approval.id
    #    return target_id

    def get_target_approval_lodgement_number(self, obj):
        lodgement_number = None
        if obj.target_approval:
            #lodgement_number = obj.proposal.approval.lodgement_number
            lodgement_number = obj.target_approval.lodgement_number
        return lodgement_number

    def get_originating_approval_lodgement_number(self, obj):
        lodgement_number = None
        if obj.originating_approval:
            lodgement_number = obj.originating_approval.lodgement_number
        return lodgement_number

    def get_site_remainders(self, proposal_apiary):
        today_local = datetime.now(pytz.timezone(TIME_ZONE)).date()

        for site in proposal_apiary.apiary_sites.all():
            print(site)

        ret_list = []
        for category in SiteCategory.CATEGORY_CHOICES:
            try:
                # Retrieve sites left
                filter_site_category = Q(site_category__name=category[0])
                filter_site_fee_type = Q(apiary_site_fee_type=ApiarySiteFeeType.objects.get(name=ApiarySiteFeeType.FEE_TYPE_APPLICATION))
                filter_applicant = Q(applicant=proposal_apiary.proposal.applicant)
                filter_proxy_applicant = Q(proxy_applicant=proposal_apiary.proposal.proxy_applicant)
                # filter_expiry = Q(date_expiry__gte=today_local)
                filter_used = Q(date_used__isnull=True)
                site_fee_remainders = ApiarySiteFeeRemainder.objects.filter(
                    filter_site_category &
                    filter_site_fee_type &
                    filter_applicant &
                    filter_proxy_applicant &
                    # filter_expiry &
                    filter_used
                ).order_by('datetime_created')  # Older comes earlier

                # Retrieve current fee
                site_category = SiteCategory.objects.get(name=category[0])
                fee = site_category.retrieve_fee_by_date_and_type(today_local, ApiarySiteFeeType.FEE_TYPE_APPLICATION)

                remainder = {
                    'category_name': category[1],
                    'remainders': site_fee_remainders.count(),
                    'fee': fee,
                }
                ret_list.append(remainder)
            except:
                pass

        return ret_list

    def get_on_site_information_list(self, obj):
        on_site_information_list = OnSiteInformation.objects.filter(
            apiary_site__in=ApiarySite.objects.filter(proposal_apiary=obj),
            datetime_deleted=None,
        ).order_by('-period_from')
        ret = OnSiteInformationSerializer(on_site_information_list, many=True).data
        return ret

    def get_checklist_answers(self, obj):
        return ApiaryChecklistAnswerSerializer(obj.apiary_checklist, many=True).data


class CreateProposalApiarySiteTransferSerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)
    originating_approval_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)

    class Meta:
        model = ProposalApiary
        # geo_field = 'location'

        fields = (
            'id',
            'title',
            'proposal_id',
            'originating_approval_id',
            # 'location',
            #'apiary_sites',
            'longitude',
            'latitude',
            #'on_site_information_list',
            #'checklist_questions',
        )
        read_only_fields = (
                'id',
                )


class SaveProposalApiarySerializer(serializers.ModelSerializer):
    proposal_id = serializers.IntegerField(
            required=True, write_only=True, allow_null=False)

    class Meta:
        model = ProposalApiary
        # geo_field = 'location'

        fields = (
            'id',
            'title',
            'proposal_id',
            # 'location',
            #'apiary_sites',
            'longitude',
            'latitude',
            #'on_site_information_list',
            #'checklist_questions',
        )
        read_only_fields = (
                'id',
                )


class TemporaryUseApiarySiteSerializer(serializers.ModelSerializer):
    proposal_apiary_temporary_use_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site = ApiarySiteSerializer(read_only=True)
    # apiary_site_approval = ApiarySiteApprovalSerializer(read_only=True)
    # apiary_site_approval_id = serializers.IntegerField(write_only=True, required=False)
    # apiary_site = serializers.SerializerMethodField()

    def validate(self, attrs):
        # TODO: check if the site is not temporary used to another person for the period
        # TODO: check if the licence is valid, etc
        return attrs

    class Meta:
        model = TemporaryUseApiarySite
        fields = (
            'id',
            'proposal_apiary_temporary_use_id',
            # 'apiary_site_approval',
            # 'apiary_site_approval_id',
            'apiary_site_id',
            'apiary_site',
            'selected',
        )


class ProposalApiaryTemporaryUseSerializer(serializers.ModelSerializer):
    # proposal_id = serializers.IntegerField(write_only=True, required=False)
    proposal_id = serializers.IntegerField(required=False)
    # loaning_approval_id = serializers.IntegerField(write_only=True, required=False)
    loaning_approval_id = serializers.IntegerField(required=False)
    temporary_use_apiary_sites = TemporaryUseApiarySiteSerializer(read_only=True, many=True)
    deed_poll_documents = serializers.SerializerMethodField()
    lodgement_number = serializers.CharField(source='proposal.lodgement_number', required=False, read_only=True)
    # customer_status = serializers.CharField(source='proposal.customer_status', required=False, read_only=True)
    customer_status = serializers.SerializerMethodField()
    processing_status = serializers.SerializerMethodField()

    def validate(self, data):
        if hasattr(self, 'context') and self.context and self.context['action'] == 'submit':
            # When this proposal is submitted, it should be validated
            field_errors = {}
            non_field_errors = []

            if not data['from_date']:
                field_errors['Period From'] = 'This field is required'
            if not data['to_date']:
                field_errors['Period To'] = 'This field is required'
            if not data['temporary_occupier_name']:
                field_errors['Temporary Occupier Name'] = 'This field is required'

            # if data['issued_on_paper']:
            #     if not data['paper_id']:
            #         non_field_errors.append('Paper ID is required')
            #     if not data['date_of_issue']:
            #         non_field_errors.append('Date of Issue is required')
            #     if not data['time_of_issue']:
            #         non_field_errors.append('Time of Issue is required')
            #     if not self.context['num_of_documents_attached']:
            #         non_field_errors.append('Paper notice is required')
            #     if not data['offender_id']:
                    # non_field_errors.append('Offender is required')

            if field_errors:
                raise serializers.ValidationError(field_errors)

            if non_field_errors:
                raise serializers.ValidationError(non_field_errors)

        return data

    def get_processing_status(self, obj):
        status = obj.proposal.processing_status
        ret = ''
        for id, value in Proposal.PROCESSING_STATUS_CHOICES:
            if id == status:
                ret = value
                break
        return ret

    def get_customer_status(self, obj):
        status = obj.proposal.customer_status
        ret = ''
        for id, value in Proposal.CUSTOMER_STATUS_CHOICES:
            if id == status:
                ret = value
                break
        return ret

    def get_deed_poll_documents(self, obj):
        url_list = []

        if obj.proposal.deed_poll_documents.all().count():
            for doc in obj.proposal.deed_poll_documents.all():
                #if self.context.get('internal', False):
                #    # count_logs = doc.access_logs.count()
                #    url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name) + viewed_text
                #else:
                #    # To detect if the external user accessing the pdf file, we make Django serve the pdf file
                #    url = '<a href="/api/sanction_outcome/{}/doc?name={}" target="_blank">{}</a>'.format(obj.id, doc.name, doc.name)
                url = '<a href="{}" target="_blank">{}</a>'.format(doc._file.url, doc.name)
                url_list.append(url)

        urls = '<br />'.join(url_list)
        return urls

    class Meta:
        model = ProposalApiaryTemporaryUse
        fields = (
            'id',
            'from_date',
            'to_date',
            'temporary_occupier_name',
            'temporary_occupier_phone',
            'temporary_occupier_mobile',
            'temporary_occupier_email',
            'proposal_id',
            'loaning_approval_id',
            'temporary_use_apiary_sites',
            'deed_poll_documents',
            'lodgement_number',
            'customer_status',
            'processing_status',
        )


class ProposalApiarySiteTransferSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProposalApiarySiteTransfer
        fields = '__all__'


class ProposalApiaryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalApiaryDocument
        fields = ('id', 'name', '_file')


class SaveProposalApiarySiteLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProposalApiary
        fields = ('id', 'title', 'proposal')


class ProposalApiaryTypeSerializer(serializers.ModelSerializer):
    readonly = serializers.SerializerMethodField(read_only=True)
    documents_url = serializers.SerializerMethodField()
    proposal_type = serializers.SerializerMethodField()
    get_history = serializers.ReadOnlyField()
    fee_invoice_url = serializers.SerializerMethodField()

    submitter = serializers.CharField(source='submitter.get_full_name')
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)

    application_type = serializers.CharField(source='application_type.name', read_only=True)
    proposal_apiary = ProposalApiarySerializer()
    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer(many=False, read_only=True)
    apiary_site_transfer = ProposalApiarySiteTransferSerializer()
    apiary_group_application_type = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'proposal_type',
                'title',
                'customer_status',
                'processing_status',
                'review_status',
                #'applicant_type',
                'applicant',
                #'org_applicant',
                #'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                #'pending_amendment_request',
                #'is_amendment_proposal',

                #'applicant_details',
                #'training_completed',
                'fee_invoice_url',
                'fee_invoice_reference',
                'fee_paid',
                'activity',
                'proposal_apiary',
                'apiary_temporary_use',
                'apiary_site_transfer',
                'apiary_group_application_type',

                )
        read_only_fields=('documents',)

    def get_documents_url(self,obj):
        return '/media/{}/proposals/{}/documents/'.format(settings.MEDIA_APP_DIR, obj.id)

    def get_readonly(self,obj):
        return obj.can_user_view
        #return False

    def get_processing_status(self,obj):
        return obj.get_processing_status_display()

    def get_review_status(self,obj):
        return obj.get_review_status_display()

    def get_customer_status(self,obj):
        return obj.get_customer_status_display()

    def get_proposal_type(self,obj):
        return obj.get_proposal_type_display()

    def get_fee_invoice_url(self,obj):
        return '/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

    def get_apiary_group_application_type(self, obj):
        return obj.apiary_group_application_type


class ApiaryReferralGroupSerializer(serializers.ModelSerializer):
    all_members_list = serializers.SerializerMethodField()
    class Meta:
        model = ApiaryReferralGroup
        fields = (
                'id',
                'name',
                'all_members_list',
                )

    def get_all_members_list(self, obj):
        serializer = EmailUserSerializer(obj.all_members, many=True)
        return serializer.data


class ApiaryProposalReferralSerializer(serializers.ModelSerializer):
    referral = serializers.CharField(source='referral.get_full_name')
    processing_status = serializers.CharField(source='get_processing_status_display')
    apiary_referral = serializers.SerializerMethodField()
    class Meta:
        model = Referral
        fields = '__all__'

    def get_apiary_referral(self, obj):
        return ApiaryReferralSerializer(obj.apiary_referral).data

class ApiaryInternalApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = (
                'id',
                'lodgement_number',
                'start_date',
                'expiry_date',
                )

# matches InternalProposalSerializer for apiary group proposals
class ApiaryInternalProposalSerializer(BaseProposalSerializer):
    # TODO next 3 commented lines - related to 'apply as an Org or as an individual'
    #applicant = ApplicantSerializer()
    #applicant = serializers.CharField(read_only=True)
    #org_applicant = OrganisationSerializer()
    #applicant = OrganisationSerializer() # for apply as Org only
    processing_status = serializers.SerializerMethodField(read_only=True)
    review_status = serializers.SerializerMethodField(read_only=True)
    customer_status = serializers.SerializerMethodField(read_only=True)
    #submitter = EmailUserAppViewSerializer()
    submitter = serializers.CharField(source='submitter.get_full_name')
    submitter_email = serializers.CharField(source='submitter.email')
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    assessor_data = serializers.SerializerMethodField()
    latest_referrals = ApiaryProposalReferralSerializer(many=True)
    allowed_assessors = EmailUserSerializer(many=True)
    approval_level_document = serializers.SerializerMethodField()
    application_type = serializers.CharField(source='application_type.name', read_only=True)
    #region = serializers.CharField(source='region.name', read_only=True)
    #district = serializers.CharField(source='district.name', read_only=True)
    #assessor_assessment=ProposalAssessmentSerializer(read_only=True)
    #referral_assessments=ProposalAssessmentSerializer(read_only=True, many=True)
    fee_invoice_url = serializers.SerializerMethodField()
    applicant = serializers.SerializerMethodField()
    applicant_type = serializers.SerializerMethodField()
    applicant_address = serializers.SerializerMethodField()
    applicant_first_name = serializers.SerializerMethodField()
    applicant_last_name = serializers.SerializerMethodField()
    applicant_phone_number = serializers.SerializerMethodField()
    applicant_mobile_number = serializers.SerializerMethodField()
    applicant_email = serializers.SerializerMethodField()

    proposal_apiary = ProposalApiarySerializer()
    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer(many=False, read_only=True)
    apiary_site_transfer = ProposalApiarySiteTransferSerializer()

    applicant_checklist = serializers.SerializerMethodField()
    apiary_group_application_type = serializers.SerializerMethodField()
    # approval = ApiaryInternalApprovalSerializer()
    approval = serializers.SerializerMethodField()

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'activity',
                'approval_level',
                'approval_level_document',
                #'region',
                #'district',
                'title',
                'data',
                'schema',
                'customer_status',
                'processing_status',
                'review_status',
                #applicant',
                #'org_applicant',
                #'proxy_applicant',
                'submitter',
                'submitter_email',
                #'applicant_type',
                'assigned_officer',
                'assigned_approver',
                'previous_application',
                'get_history',
                'lodgement_date',
                'modified_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'documents_url',
                'assessor_mode',
                'current_assessor',
                'assessor_data',
                'comment_data',
                'latest_referrals',
                'allowed_assessors',
                'proposed_issuance_approval',
                'proposed_decline_status',
                'proposaldeclineddetails',
                'permit',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'proposal_type',
                # tab field models
                #'applicant_details',
                #'assessor_assessment',
                #'referral_assessments',
                'fee_invoice_reference',
                'fee_invoice_url',
                'fee_paid',
                'applicant',
                'applicant_type',
                'proposal_apiary',
                'apiary_temporary_use',
                'apiary_site_transfer',
                'applicant_address',

                # 'apiary_checklist',
                'applicant_checklist',
                'applicant_address',
                'applicant_first_name',
                'applicant_last_name',
                'applicant_phone_number',
                'applicant_mobile_number',
                'applicant_email',
                'apiary_group_application_type',
                'approval',
                )
        read_only_fields=('documents','requirements')

    def get_approval(self, proposal):
        ret_appr = None
        if hasattr(proposal, 'proposal_apiary') and proposal.proposal_apiary:
            appr = proposal.proposal_apiary.retrieve_approval
            if appr:
                 ret_appr = ApiaryInternalApprovalSerializer(appr).data
        return ret_appr

    def get_apiary_group_application_type(self, obj):
        return obj.apiary_group_application_type

    def get_applicant_checklist(self, obj):
        checklist = []
        if hasattr(obj, 'proposal_apiary'):
            if obj.proposal_apiary and obj.proposal_apiary.apiary_checklist.all():
                for answer in obj.proposal_apiary.apiary_checklist.all():
                    serialized_answer = ApiaryChecklistAnswerSerializer(answer)
                    checklist.append(serialized_answer.data)
        return checklist

    def get_applicant_address(self, obj):
        address_serializer = None
        if obj.relevant_applicant_address:
            address_serializer = ApplicantAddressSerializer(obj.relevant_applicant_address)
            return address_serializer.data
        return address_serializer

    def get_applicant_first_name(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.first_name

    def get_applicant_last_name(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.last_name

    def get_applicant_phone_number(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.phone_number

    def get_applicant_mobile_number(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.mobile_number

    def get_applicant_email(self, obj):
        if obj.relevant_applicant and not obj.applicant:
            return obj.relevant_applicant.email

    def get_approval_level_document(self,obj):
        if obj.approval_level_document is not None:
            return [obj.approval_level_document.name,obj.approval_level_document._file.url]
        else:
            return obj.approval_level_document

    def get_assessor_mode(self,obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return {
            'assessor_mode': True,
            'has_assessor_mode': obj.has_assessor_mode(user),
            'assessor_can_assess': obj.can_assess(user),
            'assessor_level': 'assessor',
            'assessor_box_view': obj.assessor_comments_view(user)
        }

    def get_can_edit_activities(self,obj):
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        return obj.can_edit_activities(user)

    def get_readonly(self,obj):
        return True

    def get_current_assessor(self,obj):
        return {
            'id': self.context['request'].user.id,
            'name': self.context['request'].user.get_full_name(),
            'email': self.context['request'].user.email
        }

    def get_assessor_data(self,obj):
        return obj.assessor_data

    def get_reversion_ids(self,obj):
        return obj.reversion_ids[:5]

    def get_fee_invoice_url(self,obj):
        return '/payments/invoice-pdf/{}'.format(obj.fee_invoice_reference) if obj.fee_paid else None

    def get_applicant(self,obj):
        serializer = None
        if obj.relevant_applicant_type == 'organisation':
            serializer = OrganisationSerializer(obj.relevant_applicant)
        else:
            serializer = EmailUserSerializer(obj.relevant_applicant)
        return serializer.data

    def get_applicant_type(self,obj):
        return obj.relevant_applicant_type


class ApiaryReferralSerializer(serializers.ModelSerializer):
    #processing_status = serializers.CharField(source='get_processing_status_display')
    #latest_referrals = ProposalReferralSerializer(many=True)
    #can_be_completed = serializers.BooleanField()
    referral_group = ApiaryReferralGroupSerializer()
    class Meta:
        model = ApiaryReferral
        fields = (
                'id',
                'referral_group',
                )

    #def __init__(self,*args,**kwargs):
     #   super(ReferralSerializer, self).__init__(*args, **kwargs)
      #  self.fields['proposal'] = ReferralProposalSerializer(context={'request':self.context['request']})


class FullApiaryReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='get_processing_status_display')
    latest_referrals = ApiaryProposalReferralSerializer(many=True)
    can_be_completed = serializers.BooleanField()
    apiary_referral = ApiaryReferralSerializer()
    class Meta:
        model = Referral
        fields = '__all__'

    def __init__(self,*args,**kwargs):
        super(FullApiaryReferralSerializer, self).__init__(*args, **kwargs)
        self.fields['proposal'] = ApiaryReferralProposalSerializer(context={'request':self.context['request']})


class ApiaryReferralProposalSerializer(ApiaryInternalProposalSerializer):
    def get_assessor_mode(self,obj):
        # TODO check if the proposal has been accepted or declined
        request = self.context['request']
        user = request.user._wrapped if hasattr(request.user,'_wrapped') else request.user
        try:
            referral = Referral.objects.get(proposal=obj,referral=user)
        except:
            referral = None
        return {
            'assessor_mode': True,
            'assessor_can_assess': referral.can_assess_referral(user) if referral else None,
            'assessor_level': 'referral',
            'assessor_box_view': obj.assessor_comments_view(user)
        }


class SendApiaryReferralSerializer(serializers.Serializer):
    #email = serializers.EmailField()
    group_id = serializers.IntegerField()
    text = serializers.CharField(allow_blank=True)


class DTApiaryReferralSerializer(serializers.ModelSerializer):
    processing_status = serializers.CharField(source='proposal.get_processing_status_display')
    referral_status = serializers.CharField(source='get_processing_status_display')
    proposal_lodgement_date = serializers.CharField(source='proposal.lodgement_date')
    proposal_lodgement_number = serializers.CharField(source='proposal.lodgement_number')
    submitter = serializers.SerializerMethodField()
    region = serializers.CharField(source='region.name', read_only=True)
    #referral = EmailUserSerializer()
    apiary_referral = ApiaryReferralSerializer()
    class Meta:
        model = Referral
        fields = (
            'id',
            'region',
            'activity',
            'title',
            'applicant',
            'submitter',
            'processing_status',
            'referral_status',
            'lodged_on',
            'proposal',
            'can_be_processed',
            'referral',
            'proposal_lodgement_date',
            'proposal_lodgement_number',
            'referral_text',
            'apiary_referral',
        )

    def get_submitter(self,obj):
        return EmailUserSerializer(obj.proposal.submitter).data


class UserApiaryApprovalSerializer(serializers.ModelSerializer):
    apiary_approvals = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = EmailUser
        fields = (
                'id',
                'apiary_approvals',
                )

    def get_apiary_approvals(self, obj):
        originating_approval_id = self.context.get('originating_approval_id')
        print(originating_approval_id)
        #return 'apiary_approvals'
        approvals = []
        multiple_approvals = False
        individual_approvals = False
        organisation_approvals = False
        #Individual applications
        for individual_approval in obj.disturbance_proxy_approvals.filter(
                status='current', 
                apiary_approval=True
                ).exclude(id=originating_approval_id
                        ):
            #approval = Approval.objects.filter(applicant=self.proposal.applicant, status='current', apiary_approval=True).first()
            if individual_approval.apiary_approval:
                approvals.append({
                    'type': 'individual',
                    'id':individual_approval.id,
                    'lodgement_number':individual_approval.lodgement_number,
                    })
                individual_approvals = True
        #Organisation applications
        #import ipdb;ipdb.set_trace()
        user_delegations = UserDelegation.objects.filter(user=obj)
        #organisation_approvals = []
        for user_delegation in user_delegations:
            #organisation_approvals.append(user_delegation.organisation.disturbance_approvals.all())
            for organisation_approval in user_delegation.organisation.disturbance_approvals.filter(
                    status='current',
                    apiary_approval=True
                    ).exclude(id=originating_approval_id
                            ):
                if organisation_approval.apiary_approval:
                    approvals.append({
                        'type': 'organisation', 
                        'id':organisation_approval.id,
                        'lodgement_number':organisation_approval.lodgement_number,
                        })
                    organisation_approvals = True
        #approvals.append(organisation_approvals)

        if individual_approvals and organisation_approvals:
            multiple_approvals = True

        return {'approvals': approvals, 'multiple': multiple_approvals}


class ApiaryProposalRequirementSerializer(serializers.ModelSerializer):
    due_date = serializers.DateField(input_formats=['%d/%m/%Y'],required=False,allow_null=True)
    class Meta:
        model = ProposalRequirement
        fields = ('id','due_date','free_requirement','standard_requirement','standard','order','proposal','recurrence','recurrence_schedule','recurrence_pattern','requirement','is_deleted','copied_from')
        read_only_fields = ('order','requirement', 'copied_from')

