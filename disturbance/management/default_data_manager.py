import logging
from disturbance.components.proposals.models import ApiarySiteFeeType, SiteCategory

logger = logging.getLogger(__name__)


class DefaultDataManager(object):

    def __init__(self):
        # Store default ApiarySiteFeeType data
        for item in ApiarySiteFeeType.FEE_TYPE_CHOICES:
            fee_type, created = ApiarySiteFeeType.objects.get_or_create(name=item[0])
            if created:
                logger.info("Created apiary site fee type: %s" % fee_type)

        # Store default
        for item in SiteCategory.CATEGORY_CHOICES:
            site_category, created = SiteCategory.objects.get_or_create(name=item[0])
            if created:
                logger.info("Created apiary site category: %s" % site_category)

