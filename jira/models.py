from django.db import models
from django.contrib.auth.models import User
import datetime

class Sprint(models.Model):
	url = models.CharField(max_length=1024)
	start_date = models.DateField(default=datetime.date.today)
	end_date = models.DateField(default=datetime.date.today)

	class Meta:
		verbose_name_plural = "Sprint"

class Ticket(models.Model):
	url = models.CharField(max_length=1024)
	project = models.CharField(max_length=1024)
	issue_type = models.CharField(max_length=1024)
	reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reporter")
	assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignee")
	summary = models.CharField(max_length=2048)
	description = models.TextField()
	points = models.IntegerField()
	created_date = models.DateField(default=datetime.date.today)
	modified_date = models.DateTimeField(auto_now=True)
	status = models.CharField(max_length=16, default='None')
	priority = models.CharField(max_length=16, default='None')
	watchers = models.ManyToManyField(User, blank=True, related_name='watchers')
	sprint = models.ForeignKey(Sprint, models.SET_NULL, blank=True, null=True)
	sub_task = models.ManyToManyField('Ticket', blank=True, related_name='sub_tasks')

	class Meta:
		verbose_name_plural = "Ticket"

class TicketImage(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
	image = models.ImageField(upload_to='ticketimages/')

	class Meta:
		verbose_name_plural = "TicketImage"

class TicketComment(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
	creator = models.ForeignKey(User, on_delete=models.CASCADE)
	comment = models.TextField()
	ticket_comment_likes = models.ManyToManyField(User, related_name='ticket_comment_likes')
	ticket_comment_dislikes = models.ManyToManyField(User, related_name='ticket_comment_dislikes')
	date = models.DateTimeField(default=datetime.datetime.now)
	edited = models.BooleanField(default=False)

	def increase_ticket_comment_likes(self, request):
		if(request.user not in self.ticket_comment_likes.all()):
			self.ticket_comment_likes.add(request.user)
		else:
			self.ticket_comment_likes.remove(request.user)

		if(request.user in self.ticket_comment_dislikes.all()):
			self.ticket_comment_dislikes.remove(request.user)

	def increase_ticket_comment_dislikes(self, request):
		if(request.user not in self.ticket_comment_dislikes.all()):
			self.ticket_comment_dislikes.add(request.user)
		else:
			self.ticket_comment_dislikes.remove(request.user)

		if(request.user in self.ticket_comment_likes.all()):
			self.ticket_comment_likes.remove(request.user)

	class Meta:
		verbose_name_plural = "TicketComment"