from django.conf import settings

from disturbance.components.organisations.serializers import OrganisationSerializer
from disturbance.components.proposals.serializers_base import BaseProposalSerializer, ProposalReferralSerializer, \
    ProposalDeclinedDetailsSerializer, EmailUserSerializer
from disturbance.components.proposals.models import (
    Proposal,
    ProposalApiarySiteLocation,
    ProposalApiaryTemporaryUse,
    ProposalApiarySiteTransfer,
    ProposalApiaryDocument, 
    ApiarySite, 
    OnSiteInformation,
    ApiaryReferralGroup,
)

from rest_framework import serializers


class ApiarySiteSerializer(serializers.ModelSerializer):
    proposal_apiary_site_location_id = serializers.IntegerField(write_only=True,)
    site_category_id = serializers.IntegerField(write_only=True,)
    # onsiteinformation_set = OnSiteInformationSerializer(read_only=True, many=True,)

    class Meta:
        model = ApiarySite
        fields = (
            'id',
            'available',
            'site_guid',
            'proposal_apiary_site_location_id',
            'site_category_id',
        )


class OnSiteInformationSerializer(serializers.ModelSerializer):
    apiary_site_id = serializers.IntegerField(write_only=True, required=False)
    apiary_site = ApiarySiteSerializer(read_only=True)

    class Meta:
        model = OnSiteInformation
        fields = (
            'id',
            'apiary_site',
            'apiary_site_id',
            'period_from',
            'period_to',
            'comments',
        )

    def validate(self, data):
        field_errors = {}
        non_field_errors = []

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

        return data


class ProposalApiarySiteLocationSerializer(serializers.ModelSerializer):
    apiary_sites = ApiarySiteSerializer(read_only=True, many=True)
    on_site_information_list = serializers.SerializerMethodField()  # This is used for displaying OnSite table at the frontend

    class Meta:
        model = ProposalApiarySiteLocation
        # geo_field = 'location'

        fields = (
            'id',
            'title',
            'proposal',
            # 'location',
            'apiary_sites',
            'longitude',
            'latitude',
            'on_site_information_list',
        )

    def get_on_site_information_list(self, obj):
        on_site_information_list = OnSiteInformation.objects.filter(
            apiary_site__in=ApiarySite.objects.filter(proposal_apiary_site_location=obj)
        ).order_by('-period_from')
        ret = OnSiteInformationSerializer(on_site_information_list, many=True).data
        return ret


class ProposalApiaryTemporaryUseSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProposalApiaryTemporaryUse
        fields = '__all__'


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
        model = ProposalApiarySiteLocation
        fields = ('id', 'title', 'proposal')


class ProposalApiarySerializer(serializers.ModelSerializer):
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
    apiary_site_location = ProposalApiarySiteLocationSerializer()
    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer()
    apiary_site_transfer = ProposalApiarySiteTransferSerializer()

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
                'apiary_site_location',
                'apiary_temporary_use',
                'apiary_site_transfer',

                )
        read_only_fields=('documents',)

    def get_documents_url(self,obj):
        return '/media/{}/proposals/{}/documents/'.format(settings.MEDIA_APP_DIR, obj.id)

    def get_readonly(self,obj):
        return False

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


class InternalProposalApiarySerializer(BaseProposalSerializer):
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
    proposaldeclineddetails = ProposalDeclinedDetailsSerializer()
    assessor_mode = serializers.SerializerMethodField()
    current_assessor = serializers.SerializerMethodField()
    assessor_data = serializers.SerializerMethodField()
    latest_referrals = ProposalReferralSerializer(many=True)
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

    apiary_site_location = ProposalApiarySiteLocationSerializer()
    apiary_temporary_use = ProposalApiaryTemporaryUseSerializer()
    apiary_site_transfer = ProposalApiarySiteTransferSerializer()

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
                'apiary_site_location',
                'apiary_temporary_use',
                'apiary_site_transfer',
                )
        read_only_fields=('documents','requirements')

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


class ApiaryReferralGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiaryReferralGroup
        fields = (
                'id',
                'name',
                )


class SaveApiaryProposalSerializer(BaseProposalSerializer):
    assessor_data = serializers.JSONField(required=False)

    class Meta:
        model = Proposal
        fields = (
                'id',
                'application_type',
                'activity',
                'approval_level',
                'title',
                'region',
                'district',
                'tenure',
                'data',
                'assessor_data',
                'comment_data',
                'schema',
                'customer_status',
                'processing_status',
                'review_status',
                #'hard_copy',
                'applicant',
                'proxy_applicant',
                'submitter',
                'assigned_officer',
                'previous_application',
                'lodgement_date',
                'documents',
                'requirements',
                'readonly',
                'can_user_edit',
                'can_user_view',
                'reference',
                'lodgement_number',
                'lodgement_sequence',
                'can_officer_process',
                'sub_activity_level1',
                'sub_activity_level2',
                'management_area',
                )
        read_only_fields=('documents','requirements')

