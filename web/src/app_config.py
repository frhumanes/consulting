# -*- coding: utf-8 -*-
#DATE AND TIME FORMAT
TIME_FORMAT = "H:i"
DATE_FORMAT = "%d/%m/%Y"

DEFAULT_PASSWORD = '1234'


#CODES
START_CODE_AD = 'DA'
CODE_SYMTOMS_WORSENING = 'SE'
CODE_WOMAN = 'DA4.1'
CODE_MAN = 'DA4.0'
CODE_MARRIED = 'DA9.1'
CODE_STABLE_PARTNER = 'DA9.2'
CODE_DIVORCED = 'DA9.3'
CODE_WIDOW_ER = 'DA9.4'
CODE_SINGLE = 'DA9.5'
CODE_OTHER = 'DA9.6'


#ROLES
DOCTOR = 1
ADMINISTRATIVE = 2
PATIENT = 3


#STATUS USER
MARRIED = 1
STABLE_PARTNER = 2
DIVORCED = 3
WIDOW_ER = 4
SINGLE = 5
OTHER = 6


#SEX
UNISEX =0
WOMAN = 1
MAN = 2

#ACTIVE
ACTIVE = 1
DEACTIVATE = 0

#MEDICINE
BEFORE = 1
AFTER = 2


#COMPONENT
ACTIVE_INGREDIENT = 0
MEDICINE = 1

#CONSULTATION
CONCLUSION = 0


#SURVEY
PREVIOUS_STUDY = 1
INITIAL_ASSESSMENT = 2
ANXIETY_DEPRESSION_EXTENSIVE = 3
ANXIETY_DEPRESSION_SHORT = 4
VARIABLES = 9
ADHERENCE_TREATMENT = 8
BEHAVIOR_EXTENSIVE = 5
BEHAVIOR_SHORT = 6

#BLOCK
ADMINISTRATIVE_DATA = 1
PRECEDENT_RISK_FACTOR = 2
ANXIETY_DEPRESSION_EXTENSIVE = 3
ANXIETY_DEPRESSION_SHORT = 4
BEHAVIOR_EXTENSIVE = 5
BEHAVIOR_SHORT = 6

#KIND SURVEY
GENERAL = 0
EXTENSO = 1
ABREVIADO = 2

#NUM VARIABLES
DEFAULT_NUM_VARIABLES = 10

#PAGINATION
OBJECTS_PER_PAGE = 10

#ILLNESS
DEFAULT_ILLNESS = 1
ANXIETY_DEPRESSION = 2
#STATUS APPOINTMENT
UNRESOLVED = 1
DONE = 2
NOT_DONE = 3
MODIFIED = 4
MODIFIED_DONE = 5
MODIFIED_NOT_DONE = 6
MODIFIED_DELETED = 7
CANCELED = 8

#EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#only development
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = "mailer.backend.DbBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
# EMAIL_HOST_USER = 'redmine@wtelecom.es'
# EMAIL_HOST_PASSWORD = 'password'
EMAIL_HOST_USER = 'consulting3iwt2@gmail.com'
EMAIL_HOST_PASSWORD = 'prueba123'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_USE_TLS = True

#RANGES
AVE = {140:'', 200:u'importante', 300:u'bastante alto',9999:u'muy alto'}
BECK = {10:[u'No depresión', 'success'], 
		13:[u'Leve perturbación del estado de ánimo', 'info'],
		19:[u'Depresión leve', 'default'],
		30:[u'Depresión moderada', 'warning'],
		40:[u'Depresión grave', 'important'],
		999:[u'Depresión muy grave', 'inverse']}
HAMILTON = {18:[u'No ansiedad', 'success'],
			28:[u'Ansiedad leve', 'default'],
			38:[u'Ansiedad moderada', 'warning'],
			48:[u'Ansiedad grave', 'important'],
			999:[u'Ansiedad muy grave', 'inverse']}

#WKHTMLTOPDF
WKHTMLTOPDF_CMD = '/usr/local/bin/wkhtmltopdf'
WKHTMLTOPDF_CMD_OPTIONS = {'encoding': 'utf8', 
							'quiet': True,
							'margin-bottom':20,
							'margin-right':20,
							'margin-left':20,
							'margin-top':30,
							'header-spacing':10,}