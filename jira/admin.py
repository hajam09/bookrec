from django.contrib import admin

from jira.models import Sprint
from jira.models import Ticket
from jira.models import TicketComment
from jira.models import TicketImage

admin.site.register(Sprint)
admin.site.register(Ticket)
admin.site.register(TicketComment)
admin.site.register(TicketImage)