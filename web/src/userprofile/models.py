from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    SEX = (
        (1, _(u'Female')),
        (2, _(u'Male')),
    )
    STATUS = (
        (1, _(u'Married')),
        (2, _(u'Stable partner')),
        (3, _(u'Divorced')),
        (4, _(u'Widow')),
        (5, _(u'Single')),
        (6, _(u'Other')),
    )

    user = models.ForeignKey(User, unique=True)
    name = models.CharField(_(u'Name'), max_length=150)
    first_surname = models.CharField(_(u'First surname'), max_length=150)
    second_surname = models.CharField(_(u'Second surname'), max_length=150)
    sex = models.IntegerField(_(u'Sex'), choices=SEX, blank=True)
    address = models.CharField(_(u'Address'), max_length=150)
    town = models.CharField(_(u'Town'), max_length=150)
    postcode = models.IntegerField(_(u'Postcode'))
    dob = models.DateField(_(u'Date of Birth'))
    status = models.IntegerField(_(u'Status'), choices=STATUS)
    profession = models.CharField(_(u'Profession'), max_length=150)
    is_doctor = models.BooleanField()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = Profile.objects.get_or_create(user=instance)


# Adding a profile automatically when you create a user: we use a signal
post_save.connect(create_user_profile, sender=User)
