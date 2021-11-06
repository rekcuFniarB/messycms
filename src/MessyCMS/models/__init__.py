from django.conf import settings
from MessyCMS import plugins

if hasattr(settings, 'MESSYCMS_NODE_MODEL'):
    ## Developer may define own models if he wants to define additional fields and methods
    CustomBaseModel = plugins.import_module(settings.MESSYCMS_NODE_MODEL)
    class Node(CustomBaseModel):
        pass
else:
    from .abstract import MessyBase
    class Node(MessyBase):
        pass
