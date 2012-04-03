from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _


class Profile(models.Model):
    DOCTOR = 1
    ADMINISTRATIVE = 2
    PATIENT = 3

    SEX = (
        (-1, _(u'Seleccione el sexo')),
        (1, _(u'Female')),
        (2, _(u'Male')),
    )
    STATUS = (
        (-1, _(u'Seleccione el estado civil')),
        (1, _(u'Married')),
        (2, _(u'Stable partner')),
        (3, _(u'Divorced')),
        (4, _(u'Widow')),
        (5, _(u'Single')),
        (6, _(u'Other')),
    )

    ROLE = (
        (DOCTOR, _(u'Doctor')),
        (ADMINISTRATIVE, _(u'Administrative')),
        (PATIENT, _(u'Patient')),
    )
    #username is the nick with you login in app
    user = models.ForeignKey(User, unique=True)
    doctor = models.ForeignKey('self', blank=True, null=True)
    username = models.CharField(_(u'Name of User'), max_length=50, blank=True)
    name = models.CharField(_(u'Name'), max_length=150, blank=True)
    first_surname = models.CharField(_(u'First surname'), max_length=150,
                                    blank=True)
    second_surname = models.CharField(_(u'Second surname'), max_length=150,
                                        blank=True)
    nif = models.CharField(_(u"NIF"), max_length=9, blank=True)
    sex = models.IntegerField(_(u'Sex'), choices=SEX, blank=True, null=True)
    address = models.CharField(_(u'Address'), max_length=150, blank=True)
    town = models.CharField(_(u'Town'), max_length=150, blank=True)
    postcode = models.IntegerField(_(u'Postcode'), blank=True, null=True)
    dob = models.DateField(_(u'Date of Birth'), blank=True, null=True)
    status = models.IntegerField(_(u'Status'), choices=STATUS, blank=True,
                                null=True)
    phone1 = models.CharField(_(u'First Phone'), max_length=9, blank=True)
    phone2 = models.CharField(_(u'Second Phone'), max_length=9, blank=True)
    email = models.EmailField(_(u'Email'), max_length=150, blank=True)
    profession = models.CharField(_(u'Profession'), max_length=150, blank=True)
    role = models.IntegerField(_(u'Role'), choices=ROLE, blank=True,
                                null=True)

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.first_surname,
                                self.second_surname)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = Profile.objects.get_or_create(user=instance)


# Adding a profile automatically when you create a user: we use a signal
post_save.connect(create_user_profile, sender=User)
