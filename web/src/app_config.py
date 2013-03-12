# -*- coding: utf-8 -*-

#DATE AND TIME FORMAT
TIME_FORMAT = "H:i"
DATE_FORMAT = "d/m/Y"
DATE_INPUT_FORMAT = "%d/%m/%Y"

#PASSWORD
PASSWORD_MIN_LENGTH = 8
DEFAULT_PASSWORD = '1234ABCD'
# According LOPD it should be 90 (3 months)
PASSWORD_EXPIRATION_DAYS = 6 * 30
PASSWORD_WARNING_DAYS = 15


#CODES
START_CODE_AD = 'DA'
CODE_SYMPTOMS_WORSENING = 'SE'
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
UNISEX = 0
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
ANXIETY_DEPRESSION_SURVEY = 3
ADHERENCE_TREATMENT = 4
VIRTUAL_SURVEY = 5
SELF_REGISTER = 6
EPQR_SURVEY = 7
UNHOPE_SURVEY = 8
YBOCS_SURVEY = 9
OCIR_SURVEY = 10
CUSTOM = 999


#BLOCK
ADMINISTRATIVE_DATA = 1
PRECEDENT_RISK_FACTOR = 2
ANXIETY_DEPRESSION_BLOCK = 3
BEHAVIOR_BLOCK = 4
ADHERENCE_TREATMENT_BLOCK = 6
VIRTUAL_BLOCK = 7
EPQR_BLOCK = 8
UNHOPE_BLOCK = 9
YBOCS_BLOCK = 10
OCIR_BLOCK = 11


#KIND SURVEY
GENERAL = 0
EXTENSO = 1
ABREVIADO = 2

#NUM VARIABLES
DEFAULT_NUM_VARIABLES = 10

#PAGINATION
OBJECTS_PER_PAGE = 7
MAX_VISIBLE_PAGES = 5

#DAYS BEFORE TO SHOW SURVEY
DAYS_BEFORE_SURVEY = 3

#ILLNESS
DEFAULT_ILLNESS = 'O'
ANXIETY_DEPRESSION = 'V'

#STATUS APPOINTMENT
CONFIRMED = 0
RESERVED = 1
CANCELED_BY_DOCTOR = 2
CANCELED_BY_PATIENT = 3

#MAX TIME OF LIFE FOR EDITIING APPOINTMENTS
APP_EXPIRATION_DAYS = 7

#EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#only development
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#EMAIL_BACKEND = "mailer.backend.DbBackend"
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
# EMAIL_HOST_USER = 'redmine@wtelecom.es'
# EMAIL_HOST_PASSWORD = 'password'
EMAIL_HOST_USER = 'consulting3.development@gmail.com'
EMAIL_HOST_PASSWORD = 'prueba123'
DEFAULT_FROM_EMAIL = 'Consulting 3.0' #EMAIL_HOST_USER
EMAIL_USE_TLS = True

#SMS Settings
EMAIL2SMS = False
PHONE_PREFIX = '+34'
SMS_GATEWAY = '@echoemail.net'

#RANGES
AVE = {140: '', 200: u'importante', 300: u'bastante alto', 9999: u'muy alto'}
BECK = {10: [u'Depresión ausente', 'success'],
        13: [u'Leve perturbación <br>del estado de ánimo', 'info'],
        19: [u'Depresión leve', 'default'],
        30: [u'Depresión moderada', 'warning'],
        40: [u'Depresión grave', 'important'],
        63: [u'Depresión muy grave', 'inverse']}
HAMILTON = {18: [u'Ansiedad ausente', 'success'],
            28: [u'Ansiedad leve', 'default'],
            38: [u'Ansiedad moderada', 'warning'],
            48: [u'Ansiedad grave', 'important'],
            56: [u'Ansiedad muy grave', 'inverse']}
EPQR_A = {'N': {MAN: 3.70, WOMAN: 3.77},
          'E': {MAN: 2.70, WOMAN: 3.17},
          'S': {MAN: 3.75, WOMAN: 3.01},
          'P': {MAN: 1.71, WOMAN: 1.55}}
UNHOPE = {8: [u'Grado de desesperanza bajo <br>o ausente', 'success'],
          21: [u'Grado de desesperanza alto', 'important']}
SUICIDE = {4: [u'Riesgo de suicidio mínimo <br>o nulo', 'success'],
           9: [u'Riesgo leve de suicidio', 'default'],
           15: [u'Riesgo moderado de suicidio', 'warning'],
           21: [u'Riesgo alto de suicidio', 'important']}
Y_BOCS = {8: [u'Obsesión-compulsión ausente', 'success'],
          15: [u'Obsesión-compulsión leve', 'default'],
          24: [u'Obsesión-compulsión moderada ', 'warning'],
          32: [u'Obsesión-compulsión grave', 'important'],
          41: [u'Obsesión-compulsión muy grave ', 'inverse']}
OCIR = {}

#WKHTMLTOPDF
WKHTMLTOPDF_CMD = '/usr/local/bin/wkhtmltopdf'
WKHTMLTOPDF_CMD_OPTIONS = {'encoding': 'utf8',
                           'quiet': True,
                           'margin-bottom': 20,
                           'margin-right': 20,
                           'margin-left': 20,
                           'margin-top': 30,
                           'header-spacing': 10}
